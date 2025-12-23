"""
Structural Memory Strategy.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
as a BaseContextStrategy, with domain-specific adaptations for graph-structured
game design content.

This strategy extracts four types of memory structures:
- Chunks: Raw text segments (deterministic)
- Knowledge Triples: Structured relationships (LLM-extracted from descriptions)
- Atomic Facts: Indivisible information units (LLM-based from descriptions)
- Summaries: Condensed overviews (LLM-based)

Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries

Domain Adaptation (Thesis Contribution):
Unlike the paper's approach which searches across all stored memories,
this implementation uses a two-stage retrieval process:
1. Deterministic graph traversal (BFS) to identify path-relevant nodes
2. Iterative retrieval within this constrained search space

This adaptation ensures retrieval focuses on contextually relevant memories
for game design coherence evaluation while preserving the benefits of
iterative query refinement from Zeng et al. (2024).
"""

import hashlib
import logging
from typing import Any, Optional, cast

import logfire

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
    get_layer_name,
)
from pxnodes.llm.context.shared.prompts import (
    ATOMIC_FACT_EXTRACTION_PROMPT,
    KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT,
)
from pxnodes.llm.context.structural_memory.chunks import Chunk, extract_chunks
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
    extract_atomic_facts,
    extract_atomic_facts_async,
    parse_atomic_facts,
)
from pxnodes.llm.context.structural_memory.summaries import (
    SUMMARY_EXTRACTION_PROMPT,
    Summary,
    create_fallback_summary,
    extract_summary,
    extract_summary_async,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    extract_llm_triples_only,
    extract_llm_triples_only_async,
    parse_llm_triples,
)

logger = logging.getLogger(__name__)


@StrategyRegistry.register(StrategyType.STRUCTURAL_MEMORY)
class StructuralMemoryStrategy(BaseContextStrategy):
    """
    Mixed Structural Memory strategy from Zeng et al. (2024).

    Implements the full mixed memory approach with four structures:
    - Chunks: Raw text segments (deterministic)
    - Knowledge Triples: Structured relationships (LLM-extracted)
    - Atomic Facts: Indivisible information units (LLM-based)
    - Summaries: Condensed overviews (LLM-based)

    Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries

    Domain Adaptation (Two-Stage Retrieval):
    This implementation adapts the paper's approach for graph-structured
    game design content using a two-stage process:
    1. Stage 1 (Scoping): Deterministic BFS traversal identifies path-relevant nodes
    2. Stage 2 (Retrieval): Iterative retrieval searches within scoped nodes only

    This ensures retrieval focuses on contextually relevant memories while
    preserving the benefits of iterative query refinement.

    Attributes:
        embedding_model: OpenAI embedding model name
        retrieval_iterations: Number of query refinement iterations (paper default: 3)
        retrieval_top_k: Number of memories to retrieve per iteration (paper: T=50)
        use_iterative_retrieval: Enable iterative retrieval (vs direct extraction)
        skip_fact_extraction: Skip LLM-based fact extraction
        skip_summary_extraction: Skip LLM-based summary extraction
    """

    strategy_type = StrategyType.STRUCTURAL_MEMORY
    _domain_layer_cache_global: dict[str, LayerContext] = {}

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 3,
        retrieval_top_k: int = 50,
        use_iterative_retrieval: bool = True,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
        max_chunks_per_node: int = 2,
        include_chunks: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the Mixed Structural Memory strategy.

        Args:
            llm_provider: LLM for fact/summary extraction and query refinement
            embedding_model: OpenAI embedding model name
            retrieval_iterations: Number of query refinement iterations (N in paper)
            retrieval_top_k: Memories to retrieve per iteration (T in paper, default 50)
            use_iterative_retrieval: If True, use iterative retrieval from paper.
                                     If False, use direct extraction only.
            skip_fact_extraction: If True, skip LLM-based fact extraction
            skip_summary_extraction: If True, skip LLM-based summary extraction
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.embedding_model = embedding_model
        self.retrieval_iterations = retrieval_iterations
        self.retrieval_top_k = retrieval_top_k
        self.use_iterative_retrieval = use_iterative_retrieval
        self.skip_fact_extraction = skip_fact_extraction
        self.skip_summary_extraction = skip_summary_extraction
        self.max_chunks_per_node = max_chunks_per_node
        self.include_chunks = include_chunks
        self._domain_layer_cache: Optional[LayerContext] = None
        self._domain_layer_cache_key: Optional[str] = None

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build mixed structural memory context for evaluation.

        Two-Stage Retrieval Process (Domain Adaptation):
        1. Stage 1 (Scoping): Use deterministic BFS to identify path-relevant nodes
        2. Stage 2 (Retrieval): Apply iterative retrieval within scoped nodes

        This adapts Zeng et al. (2024) for graph-structured game design content,
        ensuring retrieval focuses on contextually relevant memories.

        Extracts all four memory structures from Zeng et al. (2024):
        - Chunks: Raw text segments
        - Knowledge Triples: Structured relationships
        - Atomic Facts: Indivisible information units
        - Summaries: Condensed overviews

        Args:
            scope: Evaluation scope (target node, chart, project context)
            query: Optional query for iterative retrieval refinement.
                   If not provided, generates query from target node.

        Returns:
            ContextResult with all four memory structures and formatted context
        """
        from pxnodes.llm.context.shared.graph_retrieval import (
            get_full_path,
            get_graph_slice,
        )

        # ============================================================
        # STAGE 1: Deterministic Graph Scoping (Domain Adaptation)
        # ============================================================
        # Use full path when iterative retrieval is enabled (paper setting),
        # otherwise fall back to BFS depth scoping.
        if self.use_iterative_retrieval and self.llm_provider:
            graph_slice = get_full_path(scope.target_node, scope.chart)
        else:
            # Use BFS to identify path-relevant nodes. This constrains the
            # search space for retrieval to only contextually relevant nodes.
            graph_slice = get_graph_slice(
                scope.target_node, scope.chart, depth=scope.depth
            )
        all_nodes = (
            [scope.target_node] + graph_slice.previous_nodes + graph_slice.next_nodes
        )
        scoped_node_ids = [str(n.id) for n in all_nodes]

        logger.info(
            f"Stage 1 (Scoping): Found {len(all_nodes)} path-relevant nodes "
            f"via BFS traversal (depth={scope.depth})"
        )
        logger.info(
            "structural_memory.scoped_nodes: node_count=%d, node_names=%s",
            len(all_nodes),
            [n.name for n in all_nodes],
        )

        # ============================================================
        # STAGE 2: Memory Extraction or Iterative Retrieval
        # ============================================================
        cache_key = self._build_context_cache_key(scope, all_nodes)
        cached = self._get_cached_context(cache_key)
        if cached:
            return cached

        if self.use_iterative_retrieval and self.llm_provider:
            # Use iterative retrieval from Zeng et al. (2024)
            # but SCOPED to path-relevant nodes only
            result = self._build_context_with_iterative_retrieval(
                scope, graph_slice, all_nodes, scoped_node_ids, query
            )
        else:
            # Fallback: Direct extraction without retrieval
            result = self._build_context_with_direct_extraction(
                scope, graph_slice, all_nodes
            )

        self._set_cached_context(cache_key, result)
        return result

    def _build_context_cache_key(
        self,
        scope: EvaluationScope,
        nodes: list[Any],
    ) -> str:
        """Build cache key for scoped node or project context changes."""
        from pxnodes.llm.context.change_detection import (
            compute_node_content_hash,
        )

        node_hashes = [
            f"{node.id}:{compute_node_content_hash(node, scope.chart)}"
            for node in nodes
        ]
        node_hashes_str = "\n".join(node_hashes)

        context_parts: list[str] = []
        if scope.game_concept:
            context_parts.append(scope.game_concept.content or "")
        if scope.project_pillars:
            for pillar in scope.project_pillars:
                name = getattr(pillar, "name", "") or ""
                desc = getattr(pillar, "description", "") or ""
                context_parts.append(f"{name}:{desc}")

        context_hash = hashlib.sha256("\n".join(context_parts).encode()).hexdigest()
        nodes_hash = hashlib.sha256(node_hashes_str.encode()).hexdigest()

        return (
            f"struct_mem:context:{self.strategy_type.value}:{scope.chart.id}:"
            f"{scope.target_node.id}:{nodes_hash}:{context_hash}:"
            f"{self.use_iterative_retrieval}:{self.include_chunks}:"
            f"{self.skip_fact_extraction}:{self.skip_summary_extraction}:"
            f"{self.retrieval_iterations}:{self.retrieval_top_k}"
        )

    def _get_cached_context(self, cache_key: str) -> Optional[ContextResult]:
        """Return cached context result if available."""
        from django.core.cache import cache

        cached = cache.get(cache_key)
        if not cached:
            return None
        layers = [
            LayerContext(
                layer=layer["layer"],
                layer_name=layer["layer_name"],
                content=layer["content"],
                metadata=layer.get("metadata", {}),
                positional_index=layer.get("positional_index"),
            )
            for layer in cached.get("layers", [])
        ]
        return ContextResult(
            strategy=self.strategy_type,
            context_string=cached["context_string"],
            layers=layers,
            metadata=cached.get("metadata", {}),
        )

    def _set_cached_context(self, cache_key: str, result: ContextResult) -> None:
        """Persist context result in cache."""
        from django.core.cache import cache

        cache.set(
            cache_key,
            {
                "context_string": result.context_string,
                "layers": [
                    {
                        "layer": layer.layer,
                        "layer_name": layer.layer_name,
                        "content": layer.content,
                        "metadata": layer.metadata,
                        "positional_index": layer.positional_index,
                    }
                    for layer in result.layers
                ],
                "metadata": result.metadata,
            },
            timeout=None,
        )

    def _build_context_with_iterative_retrieval(
        self,
        scope: EvaluationScope,
        graph_slice,
        all_nodes: list,
        scoped_node_ids: list[str],
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build context using iterative retrieval from Zeng et al. (2024).

        This method:
        1. Ensures memories exist in vector store for scoped nodes
        2. Generates evaluation query from target node
        3. Applies iterative retrieval WITHIN scoped nodes only
        4. Combines retrieved memories with deterministic extractions
        """
        from pxnodes.llm.context.structural_memory.retriever import (
            IterativeRetriever,
        )
        from pxnodes.llm.context.structural_memory.retriever import (
            LLMProvider as RetrieverLLMProvider,
        )

        # Generate query if not provided
        if not query:
            query = self._generate_evaluation_query(scope)

        from django.core.cache import cache

        from pxnodes.llm.context.change_detection import compute_node_content_hash
        from pxnodes.llm.context.structural_memory.retriever import (
            RetrievalResult,
            RetrievedMemory,
        )

        content_hash = compute_node_content_hash(scope.target_node, scope.chart)
        cache_key = (
            f"struct_mem:retrieval:{scope.chart.id}:"
            f"{scope.target_node.id}:{content_hash}:"
            f"{self.retrieval_iterations}:{self.retrieval_top_k}"
        )
        cached = cache.get(cache_key)
        if cached:
            retrieval_result = RetrievalResult(query=cached["query"])
            retrieval_result.refined_queries = cached.get("refined_queries", [])
            retrieval_result.iterations_performed = cached.get(
                "iterations_performed", 0
            )
            for mem in cached.get("memories", []):
                retrieval_result.memories.append(
                    RetrievedMemory(
                        id=mem["id"],
                        node_id=mem["node_id"],
                        chart_id=mem.get("chart_id"),
                        memory_type=mem["memory_type"],
                        content=mem["content"],
                        metadata=mem.get("metadata"),
                        distance=mem.get("distance", 0.0),
                    )
                )
            return self._build_context_from_retrieval(
                scope, graph_slice, all_nodes, retrieval_result
            )

        logger.info(
            f"Stage 2 (Iterative Retrieval): query='{query[:50]}...', "
            f"iterations={self.retrieval_iterations}, top_k={self.retrieval_top_k}"
        )

        # Initialize retriever
        # Cast LLMProvider since both protocols are compatible
        assert self.llm_provider is not None  # Already checked in caller
        retriever = IterativeRetriever(
            llm_provider=cast(RetrieverLLMProvider, self.llm_provider),
            embedding_model=self.embedding_model,
        )

        try:
            # Ensure vector store has memories for scoped nodes
            self._ensure_vector_store_memories(scope, all_nodes)

            # Perform iterative retrieval SCOPED to path-relevant nodes
            # This is the key domain adaptation: we don't search all memories,
            # only those belonging to nodes in the evaluation path
            retrieval_result = retriever.retrieve(
                query=query,
                node_ids=scoped_node_ids,  # ← Scope to path-relevant nodes only
                iterations=self.retrieval_iterations,
                top_k=self.retrieval_top_k,
            )

            logger.info(
                "Iterative retrieval complete: %d memories, %d iterations, %d "
                "query refinements",
                len(retrieval_result.memories),
                retrieval_result.iterations_performed,
                len(retrieval_result.refined_queries),
            )

            cache.set(
                cache_key,
                {
                    "query": retrieval_result.query,
                    "refined_queries": retrieval_result.refined_queries,
                    "iterations_performed": retrieval_result.iterations_performed,
                    "memories": [
                        {
                            "id": memory.id,
                            "node_id": memory.node_id,
                            "chart_id": memory.chart_id,
                            "memory_type": memory.memory_type,
                            "content": memory.content,
                            "metadata": memory.metadata,
                            "distance": memory.distance,
                        }
                        for memory in retrieval_result.memories
                    ],
                },
                timeout=None,
            )

            # Build context combining retrieved + deterministic data
            return self._build_context_from_retrieval(
                scope, graph_slice, all_nodes, retrieval_result
            )

        except Exception as e:
            logger.warning(
                f"Iterative retrieval failed: {e}. "
                f"Falling back to direct extraction."
            )
            return self._build_context_with_direct_extraction(
                scope, graph_slice, all_nodes
            )
        finally:
            retriever.close()

    def _ensure_vector_store_memories(
        self, scope: EvaluationScope, nodes: list
    ) -> None:
        """
        Ensure vector store has memories for scoped nodes.

        Iterative retrieval assumes knowledge triples and atomic facts exist
        in the vector store. If missing, generate and store them.
        """
        from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
        from pxnodes.llm.context.shared.vector_store import VectorStore

        if not self.llm_provider:
            return

        vector_store = VectorStore()
        to_embed: list[dict[str, Any]] = []

        from pxnodes.llm.context.change_detection import has_node_changed

        with logfire.span(
            "structural_memory.ensure_vector_store",
            node_count=len(nodes),
            chart_id=str(scope.chart.id),
        ):
            nodes_to_process: list[Any] = []
            for node in nodes:
                node_id = str(node.id)
                existing = vector_store.get_memories_by_node(
                    node_id=node_id, chart_id=str(scope.chart.id)
                )
                if existing and not has_node_changed(node, scope.chart):
                    continue
                nodes_to_process.append(node)

            node_map = {str(node.id): node for node in nodes_to_process}
            node_counts: dict[str, dict[str, int]] = {}

            for node in nodes_to_process:
                vector_store.delete_memories_by_node(
                    str(node.id), chart_id=str(scope.chart.id)
                )

            async def _extract_node_memories(node: Any) -> tuple[str, Any, Any]:
                node_id = str(node.id)
                if not self.llm_provider:
                    return node_id, [], []
                triples_task = extract_llm_triples_only_async(node, self.llm_provider)
                facts_task = extract_atomic_facts_async(
                    node,
                    self.llm_provider,
                    force_regenerate=True,
                    chart_id=str(scope.chart.id),
                )
                triples, facts = await asyncio.gather(
                    triples_task, facts_task, return_exceptions=True
                )
                return node_id, triples, facts

            def _extract_node_memories_sync(node: Any) -> tuple[str, Any, Any]:
                node_id = str(node.id)
                if not self.llm_provider:
                    return node_id, [], []
                triples = extract_llm_triples_only(node, self.llm_provider)
                facts = extract_atomic_facts(
                    node,
                    self.llm_provider,
                    force_regenerate=True,
                    chart_id=str(scope.chart.id),
                )
                return node_id, triples, facts

            results: list[Any] = []
            if nodes_to_process:
                try:
                    import asyncio

                    async def _run_parallel() -> list[Any]:
                        tasks = [
                            _extract_node_memories(node) for node in nodes_to_process
                        ]
                        return await asyncio.gather(*tasks, return_exceptions=True)

                    results = asyncio.run(_run_parallel())
                except RuntimeError:
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(_extract_node_memories_sync, node)
                            for node in nodes_to_process
                        ]
                        for future in futures:
                            try:
                                results.append(future.result())
                            except Exception as exc:
                                results.append(exc)

            for result in results:
                if isinstance(result, Exception):
                    logger.warning("Vector store extraction failed: %s", result)
                    continue
                node_id, triples, facts = result
                if isinstance(triples, Exception):
                    logger.warning("Triple extraction failed: %s", triples)
                    triples = []
                if isinstance(facts, Exception):
                    logger.warning("Fact extraction failed: %s", facts)
                    facts = []

                node_counts[node_id] = {
                    "triples": len(triples),
                    "facts": len(facts),
                }

                for triple in triples:
                    content = str(triple)
                    metadata = {
                        "head": triple.head,
                        "relation": triple.relation,
                        "tail": triple.tail,
                    }
                    to_embed.append(
                        {
                            "node_id": node_id,
                            "chart_id": str(scope.chart.id),
                            "memory_type": "knowledge_triple",
                            "content": content,
                            "metadata": metadata,
                        }
                    )

                for fact in facts:
                    to_embed.append(
                        {
                            "node_id": node_id,
                            "chart_id": str(scope.chart.id),
                            "memory_type": "atomic_fact",
                            "content": fact.fact,
                            "metadata": {"source_field": fact.source_field},
                        }
                    )

            if to_embed:
                generator = OpenAIEmbeddingGenerator(model=self.embedding_model)
                embeddings = generator.generate_embeddings_batch(
                    [item["content"] for item in to_embed]
                )

                for item, embedding in zip(to_embed, embeddings):
                    hash_input = (
                        f"{item['node_id']}:{item['chart_id']}:"
                        f"{item['memory_type']}:{item['content']}"
                    )
                    memory_id = hashlib.md5(hash_input.encode()).hexdigest()
                    vector_store.store_memory(
                        memory_id=memory_id,
                        node_id=item["node_id"],
                        memory_type=item["memory_type"],
                        content=item["content"],
                        embedding=embedding,
                        chart_id=item["chart_id"],
                        metadata=item["metadata"],
                    )

                logfire.info(
                    "structural_memory.vector_store_populated",
                    stored_count=len(to_embed),
                )
                from pxnodes.llm.context.change_detection import (
                    update_processing_state,
                )

                for node_id, counts in node_counts.items():
                    node = node_map.get(node_id)
                    if not node:
                        continue
                    update_processing_state(
                        node=node,
                        chart=scope.chart,
                        triples_count=counts.get("triples", 0),
                        facts_count=counts.get("facts", 0),
                        embeddings_count=counts.get("triples", 0)
                        + counts.get("facts", 0),
                    )
            elif node_counts:
                from pxnodes.llm.context.change_detection import (
                    update_processing_state,
                )

                for node_id, counts in node_counts.items():
                    node = node_map.get(node_id)
                    if not node:
                        continue
                    update_processing_state(
                        node=node,
                        chart=scope.chart,
                        triples_count=counts.get("triples", 0),
                        facts_count=counts.get("facts", 0),
                        embeddings_count=0,
                    )
        vector_store.close()

    def _generate_evaluation_query(self, scope: EvaluationScope) -> str:
        """
        Generate an evaluation query from the target node.

        The query is used for iterative retrieval to find relevant memories.
        """
        node = scope.target_node
        chart = scope.chart

        # Build query focusing on what we need to evaluate
        query_parts = [
            f"Evaluate coherence of '{node.name}' in {chart.name}.",
        ]

        if node.description:
            # Include first sentence of description for context
            first_sentence = node.description.split(".")[0]
            query_parts.append(f"Node description: {first_sentence}.")

        # Add component context
        components = list(node.components.select_related("definition").all()[:3])
        if components:
            comp_str = ", ".join(f"{c.definition.name}={c.value}" for c in components)
            query_parts.append(f"Components: {comp_str}.")

        return " ".join(query_parts)

    def _build_context_from_retrieval(
        self,
        scope: EvaluationScope,
        graph_slice,
        all_nodes: list,
        retrieval_result,
    ) -> ContextResult:
        """
        Build ContextResult from iterative retrieval results.

        Combines retrieved memories with deterministic extractions
        (chunks, summaries) and retrieved memories.
        """
        # Retrieved memories are already filtered to scoped nodes
        retrieved_triples: list[KnowledgeTriple] = []
        retrieved_facts: list[AtomicFact] = []

        for memory in retrieval_result.memories:
            if memory.memory_type == "knowledge_triple":
                # Parse triple from stored content
                # Content format: "(head, relation, tail)"
                retrieved_triples.append(
                    KnowledgeTriple(
                        head=memory.metadata.get("head", ""),
                        relation=memory.metadata.get("relation", ""),
                        tail=memory.metadata.get("tail", ""),
                    )
                )
            elif memory.memory_type == "atomic_fact":
                retrieved_facts.append(
                    AtomicFact(
                        node_id=memory.node_id,
                        fact=memory.content,
                        source_field="retrieved",
                    )
                )

        # Still extract chunks deterministically (they're not in vector store)
        all_chunks: list[Chunk] = []
        for node in all_nodes:
            all_chunks.extend(extract_chunks(node))

        # Use retrieved triples only (LLM-extracted in this pipeline)
        all_triples = retrieved_triples

        # Extract summaries (or use fallback) in parallel when possible
        all_summaries: list[Summary] = []
        from pxnodes.llm.context.change_detection import (
            get_processing_state_map,
            has_node_changed,
            update_summary_cache,
        )

        state_map = get_processing_state_map(scope.chart, all_nodes)
        cached_summary_map: dict[str, Summary] = {}
        nodes_needing_summary: list[Any] = []
        for node in all_nodes:
            node_id = str(node.id)
            state = state_map.get(node_id)
            if state and not has_node_changed(node, scope.chart) and state.summary_text:
                cached_summary_map[node_id] = Summary(
                    node_id=node_id,
                    content=state.summary_text,
                    source="cached",
                )
            else:
                nodes_needing_summary.append(node)

        node_lookup = {str(node.id): node for node in nodes_needing_summary}

        if self.llm_provider and not self.skip_summary_extraction:
            import asyncio
            import concurrent.futures

            async def _extract_summaries_parallel() -> list[Summary]:
                tasks = [
                    asyncio.to_thread(extract_summary, node, self.llm_provider)
                    for node in nodes_needing_summary
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                summaries: list[Summary] = []
                for result in results:
                    if isinstance(result, Summary):
                        summaries.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Summary extraction failed: {result}")
                return summaries

            with logfire.span(
                "structural_memory.extract.summaries.parallel",
                node_count=len(nodes_needing_summary),
            ):
                try:
                    all_summaries = asyncio.run(_extract_summaries_parallel())
                except RuntimeError:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(extract_summary, node, self.llm_provider)
                            for node in nodes_needing_summary
                        ]
                        for future in futures:
                            try:
                                result = future.result()
                            except Exception as exc:
                                logger.warning(f"Summary extraction failed: {exc}")
                                continue
                            if isinstance(result, Summary):
                                all_summaries.append(result)

            for summary in all_summaries:
                node = node_lookup.get(summary.node_id)
                if not node:
                    continue
                update_summary_cache(
                    node=node,
                    chart=scope.chart,
                    summary_text=summary.content,
                )
        else:
            for node in nodes_needing_summary:
                summary = create_fallback_summary(node)
                all_summaries.append(summary)
                update_summary_cache(
                    node=node,
                    chart=scope.chart,
                    summary_text=summary.content,
                )

        summary_map = {s.node_id: s for s in all_summaries}
        for node_id, node in node_lookup.items():
            if node_id in summary_map:
                continue
            summary = create_fallback_summary(node)
            summary_map[node_id] = summary
            update_summary_cache(
                node=node,
                chart=scope.chart,
                summary_text=summary.content,
            )
        for node_id, summary in cached_summary_map.items():
            summary_map[node_id] = summary

        all_summaries = [
            summary_map[str(node.id)]
            for node in all_nodes
            if str(node.id) in summary_map
        ]

        # Build context string
        context_string = self._build_context_string(
            scope,
            graph_slice,
            all_chunks,
            all_triples,
            retrieved_facts,
            all_summaries,
            include_chunks=self.include_chunks,
        )

        # Create synthetic layers
        layers = self._create_synthetic_layers(
            scope, all_chunks, all_triples, retrieved_facts, all_summaries
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            chunks=all_chunks,
            triples=all_triples,
            facts=retrieved_facts,
            summaries=all_summaries,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "previous_count": len(graph_slice.previous_nodes),
                "next_count": len(graph_slice.next_nodes),
                "chunk_count": len(all_chunks),
                "triple_count": len(all_triples),
                "fact_count": len(retrieved_facts),
                "summary_count": len(all_summaries),
                # Retrieval metadata (thesis-relevant metrics)
                "retrieval_method": "iterative",
                "retrieval_iterations": retrieval_result.iterations_performed,
                "retrieval_query_refinements": len(retrieval_result.refined_queries),
                "retrieval_memories_found": len(retrieval_result.memories),
                "retrieval_scoped_nodes": len(graph_slice.previous_nodes)
                + len(graph_slice.next_nodes)
                + 1,
                "includes_target_description": True,
            },
        )

    def _build_context_with_direct_extraction(
        self,
        scope: EvaluationScope,
        graph_slice,
        all_nodes: list,
    ) -> ContextResult:
        """
        Build context using direct extraction (no retrieval).

        This is the fallback when iterative retrieval is disabled or unavailable.
        """
        # 1. Extract CHUNKS (deterministic - raw text segments)
        all_chunks: list[Chunk] = []
        for node in all_nodes:
            all_chunks.extend(extract_chunks(node))

        # 2. Extract KNOWLEDGE TRIPLES + ATOMIC FACTS + SUMMARIES in parallel
        all_triples: list[KnowledgeTriple] = []
        all_facts: list[AtomicFact] = []
        all_summaries: list[Summary] = []

        from pxnodes.llm.context.change_detection import (
            get_processing_state_map,
            has_node_changed,
            update_summary_cache,
        )
        from pxnodes.llm.context.structural_memory.facts import (
            get_cached_facts_from_vector_store,
        )
        from pxnodes.llm.context.structural_memory.triples import (
            get_cached_triples_from_vector_store,
        )

        state_map = get_processing_state_map(scope.chart, all_nodes)
        cached_summary_map: dict[str, Summary] = {}
        nodes_needing_triples: list[Any] = []
        nodes_needing_facts: list[Any] = []
        nodes_needing_summary: list[Any] = []

        for node in all_nodes:
            node_id = str(node.id)
            changed = has_node_changed(node, scope.chart)

            if not changed:
                cached_triples = get_cached_triples_from_vector_store(
                    node_id, chart_id=str(scope.chart.id)
                )
                if cached_triples:
                    all_triples.extend(cached_triples)
                else:
                    nodes_needing_triples.append(node)

                cached_facts = get_cached_facts_from_vector_store(
                    node_id, chart_id=str(scope.chart.id)
                )
                if cached_facts:
                    all_facts.extend(cached_facts)
                else:
                    nodes_needing_facts.append(node)

                state = state_map.get(node_id)
                if state and state.summary_text:
                    cached_summary_map[node_id] = Summary(
                        node_id=node_id,
                        content=state.summary_text,
                        source="cached",
                    )
                else:
                    nodes_needing_summary.append(node)
            else:
                nodes_needing_triples.append(node)
                nodes_needing_facts.append(node)
                nodes_needing_summary.append(node)

        if self.llm_provider:
            import asyncio

            async def run_parallel_extractions() -> None:
                tasks: list[Any] = []
                if not self.llm_provider:
                    return
                triple_tasks = [
                    asyncio.to_thread(extract_llm_triples_only, node, self.llm_provider)
                    for node in nodes_needing_triples
                ]
                tasks.extend(triple_tasks)

                fact_tasks = []
                if not self.skip_fact_extraction:
                    fact_tasks = [
                        asyncio.to_thread(
                            extract_atomic_facts,
                            node,
                            self.llm_provider,
                            None,
                            True,
                            str(scope.chart.id),
                        )
                        for node in nodes_needing_facts
                    ]
                    tasks.extend(fact_tasks)

                summary_tasks = []
                if not self.skip_summary_extraction:
                    summary_tasks = [
                        asyncio.to_thread(extract_summary, node, self.llm_provider)
                        for node in nodes_needing_summary
                    ]
                    tasks.extend(summary_tasks)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                idx = 0

                triple_results = results[idx : idx + len(triple_tasks)]
                idx += len(triple_tasks)
                fact_results = results[idx : idx + len(fact_tasks)]
                idx += len(fact_tasks)
                summary_results = results[idx:]

                for result in triple_results:
                    if isinstance(result, list):
                        all_triples.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Triple extraction failed: {result}")

                for result in fact_results:
                    if isinstance(result, list):
                        all_facts.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Fact extraction failed: {result}")

                for result in summary_results:
                    if isinstance(result, Summary):
                        all_summaries.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Summary extraction failed: {result}")

            try:
                asyncio.run(run_parallel_extractions())
            except RuntimeError:
                import concurrent.futures

                for node in nodes_needing_triples:
                    all_triples.extend(
                        extract_llm_triples_only(node, self.llm_provider)
                    )
                    if not self.skip_fact_extraction:
                        all_facts.extend(
                            extract_atomic_facts(
                                node,
                                self.llm_provider,
                                force_regenerate=True,
                                chart_id=str(scope.chart.id),
                            )
                        )
                if not self.skip_summary_extraction:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(extract_summary, node, self.llm_provider)
                            for node in nodes_needing_summary
                        ]
                        for future in futures:
                            try:
                                result = future.result()
                            except Exception as exc:
                                logger.warning(f"Summary extraction failed: {exc}")
                                continue
                            if isinstance(result, Summary):
                                all_summaries.append(result)

        node_lookup = {str(node.id): node for node in nodes_needing_summary}
        for summary in all_summaries:
            maybe_node = node_lookup.get(summary.node_id)
            if not maybe_node:
                continue
            update_summary_cache(
                node=maybe_node,
                chart=scope.chart,
                summary_text=summary.content,
            )

        summary_map = {s.node_id: s for s in all_summaries}
        summary_map.update(cached_summary_map)
        for node_id, node in node_lookup.items():
            if node_id in summary_map:
                continue
            summary = create_fallback_summary(node)
            summary_map[node_id] = summary
            update_summary_cache(
                node=node,
                chart=scope.chart,
                summary_text=summary.content,
            )

        if not summary_map:
            for node in all_nodes:
                summary_map[str(node.id)] = create_fallback_summary(node)

        all_summaries = [
            summary_map[str(node.id)]
            for node in all_nodes
            if str(node.id) in summary_map
        ]

        # Build context string with all four structures
        context_string = self._build_context_string(
            scope,
            graph_slice,
            all_chunks,
            all_triples,
            all_facts,
            all_summaries,
            include_chunks=self.include_chunks,
        )

        # Create synthetic layers for compatibility with hierarchical views
        layers = self._create_synthetic_layers(
            scope, all_chunks, all_triples, all_facts, all_summaries
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            chunks=all_chunks,
            triples=all_triples,
            facts=all_facts,
            summaries=all_summaries,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "previous_count": len(graph_slice.previous_nodes),
                "next_count": len(graph_slice.next_nodes),
                "chunk_count": len(all_chunks),
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
                "summary_count": len(all_summaries),
                "retrieval_method": "direct_extraction",
                "includes_target_description": True,
            },
        )

    async def build_context_async(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Async version of build_context with parallel extraction.

        Runs atomic facts, knowledge triples, and summaries extraction
        in parallel across all path nodes for improved performance.

        Args:
            scope: Evaluation scope (target node, chart, project context)
            query: Optional query for retrieval (not used in async mode)

        Returns:
            ContextResult with all four memory structures
        """
        import asyncio

        from asgiref.sync import sync_to_async

        from pxnodes.llm.context.shared.graph_retrieval import get_full_path

        with logfire.span(
            "structural_memory.build_context_async",
            target_node=scope.target_node.name,
            chart=scope.chart.name,
        ):
            if self.use_iterative_retrieval and self.llm_provider:
                with logfire.span(
                    "structural_memory.build_context_async.iterative_retrieval",
                    target_node=scope.target_node.name,
                    chart=scope.chart.name,
                ):
                    return await asyncio.to_thread(self.build_context, scope, query)

            # ============================================================
            # STAGE 1: Full Path Traversal (NOT just neighbors)
            # ============================================================
            with logfire.span("full_path_traversal"):
                # Use get_full_path to get ALL nodes in the path, not just neighbors
                graph_slice = await sync_to_async(get_full_path, thread_sensitive=True)(
                    scope.target_node, scope.chart
                )

                # All nodes in path order: predecessors -> target -> successors
                all_nodes = (
                    graph_slice.previous_nodes
                    + [scope.target_node]
                    + graph_slice.next_nodes
                )

                logfire.info(
                    "full_path_retrieved",
                    total_nodes=len(all_nodes),
                    previous_count=len(graph_slice.previous_nodes),
                    next_count=len(graph_slice.next_nodes),
                    path_order=[n.name for n in all_nodes],
                )
                logfire.info(
                    "structural_memory.scoped_nodes",
                    node_count=len(all_nodes),
                    node_names=[n.name for n in all_nodes],
                )

            # ============================================================
            # STAGE 2: Parallel Memory Extraction
            # ============================================================

            # 1. Extract CHUNKS (deterministic - no LLM needed)
            with logfire.span("extract_chunks", node_count=len(all_nodes)):
                all_chunks: list[Chunk] = []
                for node in all_nodes:
                    chunks = await sync_to_async(extract_chunks, thread_sensitive=True)(
                        node
                    )
                    all_chunks.extend(chunks)
                logfire.info("chunks_extracted", count=len(all_chunks))

            # 2. PARALLEL: Extract knowledge triples + atomic facts + summaries
            all_triples: list[KnowledgeTriple] = []
            all_facts: list[AtomicFact] = []
            all_summaries: list[Summary] = []

            if self.llm_provider:
                with logfire.span(
                    "structural_memory.extract.triples_facts_summaries.parallel",
                    node_count=len(all_nodes),
                    extraction_types=["knowledge_triples", "atomic_facts", "summaries"],
                ):
                    # Create parallel tasks for each node
                    triple_tasks = [
                        extract_llm_triples_only_async(node, self.llm_provider)
                        for node in all_nodes
                    ]
                    fact_tasks = [
                        extract_atomic_facts_async(
                            node, self.llm_provider, force_regenerate=True
                        )
                        for node in all_nodes
                    ]
                    summary_tasks = []
                    if not self.skip_summary_extraction:
                        summary_tasks = [
                            extract_summary_async(node, self.llm_provider)
                            for node in all_nodes
                        ]

                    # Run all in parallel
                    results = await asyncio.gather(
                        *triple_tasks,
                        *fact_tasks,
                        *summary_tasks,
                        return_exceptions=True,
                    )

                    # Split results
                    triple_results = results[: len(triple_tasks)]
                    fact_results = results[
                        len(triple_tasks) : len(triple_tasks) + len(fact_tasks)
                    ]
                    summary_results: list[Any] = []
                    if summary_tasks:
                        summary_start = len(triple_tasks) + len(fact_tasks)
                        summary_results = results[summary_start:]

                    # Aggregate triples
                    for result in triple_results:
                        if isinstance(result, list):
                            all_triples.extend(result)
                        elif isinstance(result, Exception):
                            logger.warning(f"Triple extraction failed: {result}")

                    # Aggregate facts
                    for result in fact_results:
                        if isinstance(result, list):
                            all_facts.extend(result)
                        elif isinstance(result, Exception):
                            logger.warning(f"Fact extraction failed: {result}")

                    # Aggregate summaries
                    for result in summary_results:
                        if isinstance(result, Summary):
                            all_summaries.append(result)
                        elif isinstance(result, Exception):
                            logger.warning(f"Summary extraction failed: {result}")

                    logfire.info(
                        "memory_structures_extracted",
                        triple_count=len(all_triples),
                        fact_count=len(all_facts),
                        summary_count=len(all_summaries),
                    )
            else:
                # No LLM provider: no knowledge triples extracted
                all_triples = []

            if not all_summaries:
                for node in all_nodes:
                    all_summaries.append(create_fallback_summary(node))

            # ============================================================
            # STAGE 3: Build Context Result
            # ============================================================
            with logfire.span("build_context_result"):
                context_string = self._build_context_string(
                    scope,
                    graph_slice,
                    all_chunks,
                    all_triples,
                    all_facts,
                    all_summaries,
                    include_chunks=self.include_chunks,
                )

                # Pass graph_slice to avoid sync Django ORM calls in async context
                layers = self._create_synthetic_layers(
                    scope,
                    all_chunks,
                    all_triples,
                    all_facts,
                    all_summaries,
                    graph_slice=graph_slice,
                )

            return ContextResult(
                strategy=self.strategy_type,
                context_string=context_string,
                layers=layers,
                chunks=all_chunks,
                triples=all_triples,
                facts=all_facts,
                summaries=all_summaries,
                metadata={
                    "target_node_id": str(scope.target_node.id),
                    "target_node_name": scope.target_node.name,
                    "previous_count": len(graph_slice.previous_nodes),
                    "next_count": len(graph_slice.next_nodes),
                    "chunk_count": len(all_chunks),
                    "triple_count": len(all_triples),
                    "fact_count": len(all_facts),
                    "summary_count": len(all_summaries),
                    "retrieval_method": "async_parallel_extraction",
                    "includes_target_description": True,
                },
            )

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """
        Get synthetic layer context.

        Structural Memory is not inherently hierarchical, but we can
        create synthetic layers for compatibility:
        - L1: Project context (if available)
        - L2: Chart-level triples
        - L3: Path/neighbor triples
        - L4: Target node triples and facts
        """
        if layer == 1:
            return self._build_domain_layer(scope)
        elif layer == 2:
            return self._build_chart_layer(scope)
        elif layer == 3:
            return self._build_neighbor_layer(scope)
        else:  # layer == 4
            return self._build_node_layer(scope)

    def _build_context_string(
        self,
        scope: EvaluationScope,
        graph_slice,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        include_chunks: bool = True,
    ) -> str:
        """
        Build the formatted context string for LLM prompt.

        Organizes all four memory structures (Zeng et al. 2024):
        - Chunks: Raw text for full context
        - Knowledge Triples: Structured relationships
        - Atomic Facts: Indivisible information
        - Summaries: Condensed overviews
        """
        sections = []

        if scope.has_project_context:
            domain_layer = self._build_domain_layer(scope)
            sections.append("[PROJECT CONTEXT]\n" + domain_layer.content)

        # Previous nodes section
        if graph_slice.previous_nodes:
            prev_section = "[PREVIOUS NODES - Context Before Target]\n"
            for node in graph_slice.previous_nodes:
                node_id = str(node.id)
                prev_section += self._format_node_memory(
                    node.name,
                    node_id,
                    chunks,
                    triples,
                    facts,
                    summaries,
                    include_chunks=include_chunks,
                )
            sections.append(prev_section)

        # Target node section
        target_section = f"[TARGET NODE - {scope.target_node.name}]\n"
        target_node_id = str(scope.target_node.id)
        target_section += self._format_node_memory(
            scope.target_node.name,
            target_node_id,
            chunks,
            triples,
            facts,
            summaries,
            is_target=True,
            skip_derived_triples=True,
            include_chunks=include_chunks,
        )
        sections.append(target_section)

        # Computed metrics (derived triples)
        derived = [
            t
            for t in triples
            if t.relation.lower().startswith(
                ("component_delta_", "component_transition_", "component_change_")
            )
        ]
        if derived:
            metrics_section = "[COMPUTED METRICS]\n"
            seen = set()
            for t in derived:
                t_key = str(t)
                if t_key in seen:
                    continue
                seen.add(t_key)
                metrics_section += f"  - {t}\n"
            sections.append(metrics_section)

        # Next nodes section
        if graph_slice.next_nodes:
            next_section = "[NEXT NODES - Context After Target]\n"
            for node in graph_slice.next_nodes:
                node_id = str(node.id)
                next_section += self._format_node_memory(
                    node.name,
                    node_id,
                    chunks,
                    triples,
                    facts,
                    summaries,
                    include_chunks=include_chunks,
                )
            sections.append(next_section)

        return "\n".join(sections)

    def _format_node_memory(
        self,
        node_name: str,
        node_id: str,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        is_target: bool = False,
        skip_derived_triples: bool = False,
        include_chunks: bool = True,
    ) -> str:
        """
        Format all four memory structures for a single node.

        Following Zeng et al. (2024) mixed memory format.
        """
        # Filter memories for this node
        # Note: triples use node_name as head for readability
        # Other structures (chunks, facts, summaries) use node_id
        node_chunks = [c for c in chunks if c.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        if skip_derived_triples:
            node_triples = [
                t
                for t in node_triples
                if not t.relation.lower().startswith(
                    ("component_delta_", "component_transition_", "component_change_")
                )
            ]
        node_facts = [f for f in facts if f.node_id == node_id]
        node_summaries = [s for s in summaries if s.node_id == node_id]

        # Skip if no memory for this node
        if not any([node_chunks, node_triples, node_facts, node_summaries]):
            return ""

        lines = []
        if not is_target:
            lines.append(f"\n{node_name}:")

        # 1. Summary (condensed overview - most useful for quick understanding)
        if node_summaries:
            lines.append("\n  Summary:")
            for s in node_summaries:
                lines.append(f"    {s.content}")

        # 2. Knowledge Triples (structured relationships)
        if node_triples:
            lines.append("\n  Knowledge Triples:")
            seen = set()
            for t in node_triples:
                t_key = str(t)
                if t_key in seen:
                    continue
                seen.add(t_key)
                lines.append(f"    - {t}")

        # 3. Atomic Facts (indivisible information)
        if node_facts:
            lines.append("\n  Atomic Facts:")
            for f in node_facts:
                lines.append(f"    - {f.fact}")

        # 4. Chunks (raw text segments)
        if include_chunks:
            desc_chunks = [c for c in node_chunks if c.source == "description"]
            if desc_chunks:
                lines.append("\n  Chunks:")
                for c in desc_chunks[: self.max_chunks_per_node]:
                    # Indent multi-line content
                    content = c.content.replace("\n", "\n    ")
                    lines.append(f"    {content}")

        # Add trailing newline for spacing between nodes/sections
        lines.append("")

        return "\n".join(lines)

    def _create_synthetic_layers(
        self,
        scope: EvaluationScope,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        graph_slice: Optional[Any] = None,
    ) -> list[LayerContext]:
        """
        Create synthetic hierarchy layers for compatibility.

        Maps mixed memory structures to hierarchical layers:
        - L1 Domain: Project context (pillars, game concept)
        - L2 Category: Chart-level context
        - L3 Trace: Neighbor nodes summary
        - L4 Episode: Target node with all four memory types

        Args:
            scope: Evaluation scope
            chunks: Extracted chunks
            triples: Extracted triples
            facts: Extracted facts
            summaries: Extracted summaries
            graph_slice: Optional pre-fetched graph slice (to avoid sync calls in async)
        """
        # Store for use in layer building
        self._current_chunks = chunks
        self._current_triples = triples
        self._current_facts = facts
        self._current_summaries = summaries

        layers = []

        # L1 Domain (if project context available)
        if scope.has_project_context:
            layers.append(self._build_domain_layer(scope))

        # L2 Category (chart level)
        layers.append(self._build_chart_layer(scope))

        # L3 Trace (neighbor overview)
        layers.append(self._build_neighbor_layer(scope, graph_slice=graph_slice))

        # L4 Episode (node level with all memory structures)
        # Pass pre-computed triples to avoid sync DB call in async context
        layers.append(self._build_node_layer(scope, triples=triples))

        return layers

    def _build_domain_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L1 Domain layer using mixed memory for concept and pillars."""
        cache_key_parts = []
        concept_text = ""
        if scope.game_concept:
            concept_text = scope.game_concept.content or ""
        cache_key_parts.append(concept_text)

        if scope.project_pillars:
            for pillar in scope.project_pillars:
                name = getattr(pillar, "name", "") or ""
                desc = getattr(pillar, "description", "") or ""
                cache_key_parts.append(f"{name}:{desc}")

        cache_key = hashlib.sha256("\n".join(cache_key_parts).encode()).hexdigest()
        cached = self._domain_layer_cache_global.get(cache_key)
        if cached:
            return cached

        content_parts = []

        def chunk_text(text: str, max_size: int = 500) -> list[str]:
            if not text:
                return []
            text = text.strip()
            return [text[i : i + max_size] for i in range(0, len(text), max_size)]

        def summarize_text(title: str, description: str) -> str:
            if not self.llm_provider:
                return description.split(".")[0][:200].strip() if description else "N/A"
            prompt = SUMMARY_EXTRACTION_PROMPT.format(
                title=title,
                description=description or "No description provided.",
                components="- No components attached",
            )
            try:
                response = self.llm_provider.generate(prompt)
                return response.strip() or "N/A"
            except Exception as exc:
                logger.warning(f"Domain summary extraction failed: {exc}")
                return description.split(".")[0][:200].strip() if description else "N/A"

        def extract_domain_facts(title: str, description: str) -> list[str]:
            if not self.llm_provider or self.skip_fact_extraction:
                return []
            prompt = ATOMIC_FACT_EXTRACTION_PROMPT.format(
                title=title,
                description=description or "No description provided.",
                components="- No components attached",
            )
            try:
                response = self.llm_provider.generate(prompt)
                return parse_atomic_facts(response)
            except Exception as exc:
                logger.warning(f"Domain fact extraction failed: {exc}")
                return []

        def extract_domain_triples(title: str, description: str) -> list[str]:
            if not self.llm_provider:
                return []
            prompt = KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT.format(
                title=title,
                description=description or "No description provided.",
                components="- No components attached",
            )
            try:
                response = self.llm_provider.generate(prompt)
                triples = parse_llm_triples(response)
                return [str(t) for t in triples]
            except Exception as exc:
                logger.warning(f"Domain triple extraction failed: {exc}")
                return []

        def build_mixed_block(title: str, text: str) -> list[str]:
            if not text:
                return []
            summary = summarize_text(title, text)
            facts = extract_domain_facts(title, text)
            triples = extract_domain_triples(title, text)
            chunks = chunk_text(text) if self.include_chunks else []

            lines = [f"{title}:", f"Summary: {summary}"]
            if triples:
                lines.append("Knowledge Triples:")
                for t in triples[:8]:
                    lines.append(f"- {t}")
            if facts:
                lines.append("Atomic Facts:")
                for f in facts[:10]:
                    lines.append(f"- {f}")
            if chunks and self.include_chunks:
                lines.append("Chunks:")
                for c in chunks[: self.max_chunks_per_node]:
                    lines.append(f"- {c}")
            return lines

        entries: list[tuple[str, str]] = []
        if scope.game_concept:
            entries.append(("Game Concept", scope.game_concept.content or ""))
        if scope.project_pillars:
            for pillar in scope.project_pillars:
                name = getattr(pillar, "name", "") or "Pillar"
                desc = getattr(pillar, "description", "") or ""
                entries.append((f"Pillar: {name}", desc))

        if entries:
            try:
                import asyncio
                import concurrent.futures

                async def run_parallel() -> list[Any]:
                    with logfire.span(
                        "structural_memory.domain_mixed.parallel",
                        entry_count=len(entries),
                    ):
                        tasks = [
                            asyncio.to_thread(build_mixed_block, title, text)
                            for title, text in entries
                        ]
                        return await asyncio.gather(*tasks, return_exceptions=True)

                results = asyncio.run(run_parallel())
            except RuntimeError:
                results = []
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [
                        executor.submit(build_mixed_block, title, text)
                        for title, text in entries
                    ]
                    for future in futures:
                        try:
                            results.append(future.result())
                        except Exception as exc:
                            logger.warning(f"Domain mixed block failed: {exc}")
                            results.append([])

            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Domain mixed block failed: {result}")
                    continue
                content_parts.extend(result)

        layer = LayerContext(
            layer=1,
            layer_name=get_layer_name(1),
            content=(
                "\n".join(content_parts) if content_parts else "No project context"
            ),
            metadata={"source": "project_config", "mixed_memory": True},
        )
        self._domain_layer_cache_global[cache_key] = layer
        self._domain_layer_cache = layer
        self._domain_layer_cache_key = cache_key
        return layer

    def _build_chart_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L2 Category layer from chart."""
        chart = scope.chart
        content = f"Chart: {chart.name}\nDescription: {chart.description or 'N/A'}"
        return LayerContext(
            layer=2,
            layer_name=get_layer_name(2),
            content=content,
            metadata={"chart_id": str(chart.id)},
        )

    def _build_neighbor_layer(
        self,
        scope: EvaluationScope,
        graph_slice: Optional[Any] = None,
    ) -> LayerContext:
        """Build L3 Trace layer from neighbors.

        Args:
            scope: Evaluation scope
            graph_slice: Optional pre-fetched graph slice (avoids sync call in async)
        """
        if graph_slice is None:
            from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice

            graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=1)

        prev_names = [n.name for n in graph_slice.previous_nodes]
        next_names = [n.name for n in graph_slice.next_nodes]

        content = f"Previous: {', '.join(prev_names) or 'None'}\n"
        content += f"Next: {', '.join(next_names) or 'None'}"

        return LayerContext(
            layer=3,
            layer_name=get_layer_name(3),
            content=content,
            metadata={
                "previous_count": len(prev_names),
                "next_count": len(next_names),
            },
        )

    def _build_node_layer(
        self,
        scope: EvaluationScope,
        triples: Optional[list[KnowledgeTriple]] = None,
    ) -> LayerContext:
        """Build L4 Episode layer from target node.

        Args:
            scope: Evaluation scope
            triples: Optional pre-computed triples (avoids sync call in async)
        """
        node = scope.target_node

        # Use pre-computed triples if provided, otherwise extract
        if triples is None:
            node_triples = []
            if self.llm_provider:
                node_triples = extract_llm_triples_only(node, self.llm_provider)
        else:
            # Filter triples for this node
            node_triples = [t for t in triples if t.head == node.name]

        content_parts = [
            f"Node: {node.name}",
            f"Description: {node.description or 'N/A'}",
            "",
            "Knowledge Triples:",
        ]
        for t in node_triples[:10]:  # Limit to avoid huge context
            content_parts.append(f"  - {t}")

        return LayerContext(
            layer=4,
            layer_name=get_layer_name(4),
            content="\n".join(content_parts),
            metadata={"node_id": str(node.id), "triple_count": len(node_triples)},
        )

    @property
    def requires_embeddings(self) -> bool:
        """Structural Memory uses vector embeddings for retrieval."""
        return True

    @property
    def requires_llm(self) -> bool:
        """Requires LLM for atomic fact extraction (unless skipped)."""
        return not self.skip_fact_extraction


@StrategyRegistry.register(StrategyType.SIMPLE_SM)
class SimpleStructuralMemoryStrategy(StructuralMemoryStrategy):
    """
    Simple Structural Memory strategy.

    Uses full-path context and replaces raw descriptions with
    summaries, knowledge triples, and atomic facts only.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        **kwargs: Any,
    ):
        kwargs.pop("include_chunks", None)
        kwargs.pop("use_iterative_retrieval", None)
        super().__init__(
            llm_provider=llm_provider,
            use_iterative_retrieval=False,
            include_chunks=False,
            **kwargs,
        )

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build simple structural memory context for evaluation.

        Full-path traversal + summaries/triples/facts only (no chunks).
        """
        from pxnodes.llm.context.shared.graph_retrieval import get_full_path

        graph_slice = get_full_path(scope.target_node, scope.chart)
        all_nodes = (
            graph_slice.previous_nodes + [scope.target_node] + graph_slice.next_nodes
        )

        cache_key = self._build_context_cache_key(scope, all_nodes)
        cached = self._get_cached_context(cache_key)
        if cached:
            return cached

        all_triples: list[KnowledgeTriple] = []
        all_facts: list[AtomicFact] = []
        all_summaries: list[Summary] = []

        from pxnodes.llm.context.change_detection import (
            get_processing_state_map,
            has_node_changed,
            update_summary_cache,
        )
        from pxnodes.llm.context.structural_memory.facts import (
            get_cached_facts_from_vector_store,
        )
        from pxnodes.llm.context.structural_memory.triples import (
            get_cached_triples_from_vector_store,
        )

        state_map = get_processing_state_map(scope.chart, all_nodes)
        cached_summary_map: dict[str, Summary] = {}
        nodes_needing_triples: list[Any] = []
        nodes_needing_facts: list[Any] = []
        nodes_needing_summary: list[Any] = []

        for node in all_nodes:
            node_id = str(node.id)
            changed = has_node_changed(node, scope.chart)

            if not changed:
                cached_triples = get_cached_triples_from_vector_store(
                    node_id, chart_id=str(scope.chart.id)
                )
                if cached_triples:
                    all_triples.extend(cached_triples)
                else:
                    nodes_needing_triples.append(node)

                cached_facts = get_cached_facts_from_vector_store(
                    node_id, chart_id=str(scope.chart.id)
                )
                if cached_facts:
                    all_facts.extend(cached_facts)
                else:
                    nodes_needing_facts.append(node)

                state = state_map.get(node_id)
                if state and state.summary_text:
                    cached_summary_map[node_id] = Summary(
                        node_id=node_id,
                        content=state.summary_text,
                        source="cached",
                    )
                else:
                    nodes_needing_summary.append(node)
            else:
                nodes_needing_triples.append(node)
                nodes_needing_facts.append(node)
                nodes_needing_summary.append(node)

        if self.llm_provider:
            import asyncio

            async def run_parallel_extractions() -> None:
                tasks: list[Any] = []
                if not self.llm_provider:
                    return
                triple_tasks = [
                    asyncio.to_thread(extract_llm_triples_only, node, self.llm_provider)
                    for node in nodes_needing_triples
                ]
                tasks.extend(triple_tasks)

                fact_tasks = []
                if not self.skip_fact_extraction:
                    fact_tasks = [
                        asyncio.to_thread(
                            extract_atomic_facts,
                            node,
                            self.llm_provider,
                            None,
                            True,
                            str(scope.chart.id),
                        )
                        for node in nodes_needing_facts
                    ]
                    tasks.extend(fact_tasks)

                summary_tasks = []
                if not self.skip_summary_extraction:
                    summary_tasks = [
                        asyncio.to_thread(extract_summary, node, self.llm_provider)
                        for node in nodes_needing_summary
                    ]
                    tasks.extend(summary_tasks)

                results = await asyncio.gather(*tasks, return_exceptions=True)
                idx = 0

                triple_results = results[idx : idx + len(triple_tasks)]
                idx += len(triple_tasks)
                fact_results = results[idx : idx + len(fact_tasks)]
                idx += len(fact_tasks)
                summary_results = results[idx:]

                for result in triple_results:
                    if isinstance(result, list):
                        all_triples.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Triple extraction failed: {result}")

                for result in fact_results:
                    if isinstance(result, list):
                        all_facts.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Fact extraction failed: {result}")

                for result in summary_results:
                    if isinstance(result, Summary):
                        all_summaries.append(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Summary extraction failed: {result}")

            try:
                asyncio.run(run_parallel_extractions())
            except RuntimeError:
                import concurrent.futures

                for node in nodes_needing_triples:
                    all_triples.extend(
                        extract_llm_triples_only(node, self.llm_provider)
                    )
                    if not self.skip_fact_extraction:
                        all_facts.extend(
                            extract_atomic_facts(
                                node,
                                self.llm_provider,
                                force_regenerate=True,
                                chart_id=str(scope.chart.id),
                            )
                        )
                if not self.skip_summary_extraction:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        futures = [
                            executor.submit(extract_summary, node, self.llm_provider)
                            for node in nodes_needing_summary
                        ]
                        for future in futures:
                            try:
                                result = future.result()
                            except Exception as exc:
                                logger.warning(f"Summary extraction failed: {exc}")
                                continue
                            if isinstance(result, Summary):
                                all_summaries.append(result)

        node_lookup = {str(node.id): node for node in nodes_needing_summary}
        for summary in all_summaries:
            maybe_node = node_lookup.get(summary.node_id)
            if not maybe_node:
                continue
            update_summary_cache(
                node=maybe_node,
                chart=scope.chart,
                summary_text=summary.content,
            )

        summary_map = {s.node_id: s for s in all_summaries}
        summary_map.update(cached_summary_map)
        for node_id, node in node_lookup.items():
            if node_id in summary_map:
                continue
            summary = create_fallback_summary(node)
            summary_map[node_id] = summary
            update_summary_cache(
                node=node,
                chart=scope.chart,
                summary_text=summary.content,
            )

        if not summary_map:
            for node in all_nodes:
                summary_map[str(node.id)] = create_fallback_summary(node)

        all_summaries = [
            summary_map[str(node.id)]
            for node in all_nodes
            if str(node.id) in summary_map
        ]

        context_string = self._build_context_string(
            scope,
            graph_slice,
            [],
            all_triples,
            all_facts,
            all_summaries,
            include_chunks=False,
        )

        layers = self._create_synthetic_layers(
            scope,
            [],
            all_triples,
            all_facts,
            all_summaries,
            graph_slice=graph_slice,
        )

        ctx_result = ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            chunks=[],
            triples=all_triples,
            facts=all_facts,
            summaries=all_summaries,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "previous_count": len(graph_slice.previous_nodes),
                "next_count": len(graph_slice.next_nodes),
                "chunk_count": 0,
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
                "summary_count": len(all_summaries),
                "retrieval_method": "simple_structural_memory",
                "includes_target_description": True,
            },
        )

        self._set_cached_context(cache_key, ctx_result)
        return ctx_result

    async def build_context_async(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        import asyncio

        return await asyncio.to_thread(self.build_context, scope, query)

    @property
    def requires_embeddings(self) -> bool:
        """Simple SM does not use vector embeddings."""
        return False
