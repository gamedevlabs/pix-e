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
This implementation mirrors the full-context baseline while applying mixed
structural memory and optional iterative retrieval across all chart nodes.
"""

import hashlib
import logging
from typing import Any, Optional, cast

import logfire

from pxnodes.llm.context.artifacts import (
    ARTIFACT_CHUNKS,
    ARTIFACT_EDGE_TRIPLES,
    ARTIFACT_FACTS,
    ARTIFACT_SUMMARY,
    ARTIFACT_TRIPLES,
    ArtifactInventory,
)
from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
    get_layer_name,
)
from pxnodes.llm.context.structural_memory.chunks import Chunk
from pxnodes.llm.context.structural_memory.facts import AtomicFact
from pxnodes.llm.context.structural_memory.summaries import Summary
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    extract_llm_triples_only,
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
    1. Stage 1 (Scoping): Use full chart nodes for baseline parity
    2. Stage 2 (Retrieval): Iterative retrieval searches within all chart nodes

    This keeps the context scope consistent with Full Context while
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
        retrieval_max_distance: Optional[float] = 2.0,
        use_iterative_retrieval: bool = True,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
        max_chunks_per_node: int = 2,
        include_chunks: bool = True,
        use_full_chart_context: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the Mixed Structural Memory strategy.

        Args:
            llm_provider: LLM for fact/summary extraction and query refinement
            embedding_model: OpenAI embedding model name
            retrieval_iterations: Number of query refinement iterations (N in paper)
            retrieval_top_k: Memories to retrieve per iteration (T in paper, default 50)
            retrieval_max_distance: Maximum distance to keep retrieved memories
            use_iterative_retrieval: If True, use iterative retrieval from paper.
                                     If False, use direct extraction only.
            skip_fact_extraction: If True, skip LLM-based fact extraction
            skip_summary_extraction: If True, skip LLM-based summary extraction
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.embedding_model = embedding_model
        self.retrieval_iterations = retrieval_iterations
        self.retrieval_top_k = retrieval_top_k
        self.retrieval_max_distance = retrieval_max_distance
        self.use_iterative_retrieval = use_iterative_retrieval
        self.skip_fact_extraction = skip_fact_extraction
        self.skip_summary_extraction = skip_summary_extraction
        self.max_chunks_per_node = max_chunks_per_node
        self.include_chunks = include_chunks
        self.use_full_chart_context = use_full_chart_context
        self._domain_layer_cache: Optional[LayerContext] = None
        self._domain_layer_cache_key: Optional[str] = None

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build mixed structural memory context for evaluation.

        Two-Stage Retrieval Process:
        1. Stage 1 (Scoping): Use the full chart node set (no path scoping)
        2. Stage 2 (Retrieval): Apply iterative retrieval within all chart nodes

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
        # ============================================================
        # STAGE 1: Deterministic Graph Scoping (Full chart baseline)
        # ============================================================
        containers = scope.chart.containers.select_related("content").all()
        all_nodes = [c.content for c in containers if c.content is not None]
        if scope.target_node not in all_nodes:
            all_nodes.append(scope.target_node)

        edge_triples = self._load_chart_edge_triples(scope.chart)
        scoped_node_ids = [str(n.id) for n in all_nodes]

        logger.info(
            "Stage 1 (Scoping): Using full chart nodes (count=%d) with no path scoping",
            len(all_nodes),
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
            # but SCOPED to all chart nodes for baseline parity
            result = self._build_context_with_iterative_retrieval(
                scope,
                all_nodes,
                scoped_node_ids,
                edge_triples,
                query,
            )
        else:
            # Fallback: Direct extraction without retrieval
            result = self._build_context_with_direct_extraction(
                scope, all_nodes, edge_triples
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

    def _load_node_artifacts(
        self,
        scope: EvaluationScope,
        nodes: list[Any],
        include_chunks: bool,
        include_triples: bool,
        include_facts: bool,
        include_summaries: bool,
        allow_llm_summaries: bool,
    ) -> tuple[list[Chunk], list[KnowledgeTriple], list[AtomicFact], list[Summary]]:
        inventory = ArtifactInventory(
            self.llm_provider, allow_llm_summaries=allow_llm_summaries
        )
        artifact_types: list[str] = []
        if include_chunks:
            artifact_types.append(ARTIFACT_CHUNKS)
        if include_triples:
            artifact_types.append(ARTIFACT_TRIPLES)
        if include_facts:
            artifact_types.append(ARTIFACT_FACTS)
        if include_summaries:
            artifact_types.append(ARTIFACT_SUMMARY)

        if not artifact_types:
            return [], [], [], []

        node_artifacts = inventory.get_or_build_node_artifacts(
            chart=scope.chart, nodes=nodes, artifact_types=artifact_types
        )

        all_chunks: list[Chunk] = []
        all_triples: list[KnowledgeTriple] = []
        all_facts: list[AtomicFact] = []
        all_summaries: list[Summary] = []

        for node in nodes:
            node_id = str(node.id)
            artifacts = node_artifacts.get(node_id, [])
            for artifact in artifacts:
                if artifact.artifact_type == ARTIFACT_CHUNKS:
                    for chunk in artifact.content or []:
                        content = chunk.get("content", "")
                        source = chunk.get("source", "description")
                        all_chunks.append(
                            Chunk(node_id=node_id, content=content, source=source)
                        )
                elif artifact.artifact_type == ARTIFACT_TRIPLES:
                    for triple in artifact.content or []:
                        all_triples.append(
                            KnowledgeTriple(
                                head=triple.get("head", ""),
                                relation=triple.get("relation", ""),
                                tail=triple.get("tail", ""),
                            )
                        )
                elif artifact.artifact_type == ARTIFACT_FACTS:
                    for fact in artifact.content or []:
                        all_facts.append(
                            AtomicFact(
                                node_id=node_id,
                                fact=fact.get("fact", ""),
                                source_field=fact.get("source_field", "description"),
                            )
                        )
                elif artifact.artifact_type == ARTIFACT_SUMMARY:
                    content = artifact.content or ""
                    all_summaries.append(
                        Summary(node_id=node_id, content=content, source="artifact")
                    )

        return all_chunks, all_triples, all_facts, all_summaries

    def _load_chart_edge_triples(self, chart: Any) -> list[KnowledgeTriple]:
        inventory = ArtifactInventory(self.llm_provider)
        artifacts = inventory.get_or_build_chart_artifacts(
            chart=chart,
            artifact_types=[ARTIFACT_EDGE_TRIPLES],
        )
        edge_triples: list[KnowledgeTriple] = []
        for artifact in artifacts:
            if artifact.artifact_type != ARTIFACT_EDGE_TRIPLES:
                continue
            for triple in artifact.content or []:
                edge_triples.append(
                    KnowledgeTriple(
                        head=triple.get("head", ""),
                        relation=triple.get("relation", ""),
                        tail=triple.get("tail", ""),
                    )
                )
        return edge_triples

    def _build_context_with_iterative_retrieval(
        self,
        scope: EvaluationScope,
        all_nodes: list,
        scoped_node_ids: list[str],
        edge_triples: list[KnowledgeTriple],
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
            f"{self.retrieval_iterations}:{self.retrieval_top_k}:"
            f"{self.retrieval_max_distance}"
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
                scope, all_nodes, edge_triples, retrieval_result
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

            # Perform iterative retrieval across all chart nodes
            retrieval_result = retriever.retrieve(
                query=query,
                node_ids=scoped_node_ids,  # Scoped to full chart for baseline parity
                iterations=self.retrieval_iterations,
                top_k=self.retrieval_top_k,
                max_distance=self.retrieval_max_distance,
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
                scope, all_nodes, edge_triples, retrieval_result
            )

        except Exception as e:
            logger.warning(
                f"Iterative retrieval failed: {e}. "
                f"Falling back to direct extraction."
            )
            return self._build_context_with_direct_extraction(
                scope, all_nodes, edge_triples
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
                has_edge_triples = any(
                    mem.get("memory_type") == "knowledge_triple"
                    and mem.get("metadata", {}).get("source") == "edge"
                    for mem in existing
                )
                if (
                    existing
                    and not has_node_changed(node, scope.chart)
                    and has_edge_triples
                ):
                    continue
                nodes_to_process.append(node)

            node_map = {str(node.id): node for node in nodes_to_process}
            node_counts: dict[str, dict[str, int]] = {}

            for node in nodes_to_process:
                vector_store.delete_memories_by_node(
                    str(node.id), chart_id=str(scope.chart.id)
                )
            if nodes_to_process:
                inventory = ArtifactInventory(self.llm_provider)
                artifact_types = [ARTIFACT_TRIPLES]
                if not self.skip_fact_extraction:
                    artifact_types.append(ARTIFACT_FACTS)
                node_artifacts = inventory.get_or_build_node_artifacts(
                    chart=scope.chart,
                    nodes=nodes_to_process,
                    artifact_types=artifact_types,
                )
                edge_artifacts = inventory.get_or_build_chart_artifacts(
                    chart=scope.chart,
                    artifact_types=[ARTIFACT_EDGE_TRIPLES],
                )
                edge_triples_by_source: dict[str, list[dict[str, Any]]] = {}
                for artifact in edge_artifacts:
                    if artifact.artifact_type != ARTIFACT_EDGE_TRIPLES:
                        continue
                    for triple in artifact.content or []:
                        source_node_id = triple.get("source_node_id") or ""
                        if not source_node_id:
                            continue
                        edge_triples_by_source.setdefault(source_node_id, []).append(
                            triple
                        )

                for node in nodes_to_process:
                    node_id = str(node.id)
                    triples_data: list[dict[str, Any]] = []
                    facts_data: list[dict[str, Any]] = []
                    for artifact in node_artifacts.get(node_id, []):
                        if artifact.artifact_type == ARTIFACT_TRIPLES:
                            triples_data = artifact.content or []
                        elif artifact.artifact_type == ARTIFACT_FACTS:
                            facts_data = artifact.content or []
                    edge_triples_data = edge_triples_by_source.get(node_id, [])

                    node_counts[node_id] = {
                        "triples": len(triples_data) + len(edge_triples_data),
                        "facts": len(facts_data),
                    }

                    for triple in triples_data:
                        head = triple.get("head", "")
                        relation = triple.get("relation", "")
                        tail = triple.get("tail", "")
                        content = triple.get("text") or f"({head}, {relation}, {tail})"
                        to_embed.append(
                            {
                                "node_id": node_id,
                                "chart_id": str(scope.chart.id),
                                "memory_type": "knowledge_triple",
                                "content": content,
                                "metadata": {
                                    "head": head,
                                    "relation": relation,
                                    "tail": tail,
                                },
                            }
                        )

                    for triple in edge_triples_data:
                        head = triple.get("head", "")
                        relation = triple.get("relation", "")
                        tail = triple.get("tail", "")
                        content = triple.get("text") or f"({head}, {relation}, {tail})"
                        to_embed.append(
                            {
                                "node_id": node_id,
                                "chart_id": str(scope.chart.id),
                                "memory_type": "knowledge_triple",
                                "content": content,
                                "metadata": {
                                    "head": head,
                                    "relation": relation,
                                    "tail": tail,
                                    "source_node_id": triple.get("source_node_id", ""),
                                    "target_node_id": triple.get("target_node_id", ""),
                                    "source": "edge",
                                },
                            }
                        )

                    for fact in facts_data:
                        to_embed.append(
                            {
                                "node_id": node_id,
                                "chart_id": str(scope.chart.id),
                                "memory_type": "atomic_fact",
                                "content": fact.get("fact", ""),
                                "metadata": {
                                    "source_field": fact.get(
                                        "source_field", "description"
                                    )
                                },
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
        all_nodes: list,
        edge_triples: list[KnowledgeTriple],
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

        from pxnodes.llm.context.structural_memory.facts import (
            get_cached_facts_from_vector_store,
        )
        from pxnodes.llm.context.structural_memory.triples import (
            get_cached_triples_from_vector_store,
        )

        target_triples = get_cached_triples_from_vector_store(
            str(scope.target_node.id), chart_id=str(scope.chart.id)
        )
        target_facts = get_cached_facts_from_vector_store(
            str(scope.target_node.id), chart_id=str(scope.chart.id)
        )

        if target_triples:
            seen = {str(t) for t in retrieved_triples}
            for t in target_triples:
                if str(t) not in seen:
                    retrieved_triples.append(t)
                    seen.add(str(t))

        if target_facts:
            seen = {f.fact for f in retrieved_facts}
            for f in target_facts:
                if f.fact not in seen:
                    retrieved_facts.append(f)
                    seen.add(f.fact)

        # Use retrieved triples only (LLM-extracted in this pipeline)
        all_triples = retrieved_triples

        all_chunks, _, _, all_summaries = self._load_node_artifacts(
            scope=scope,
            nodes=all_nodes,
            include_chunks=self.include_chunks,
            include_triples=False,
            include_facts=False,
            include_summaries=True,
            allow_llm_summaries=not self.skip_summary_extraction,
        )

        # Build context string
        context_string = self._build_full_chart_context_string(
            scope=scope,
            nodes=all_nodes,
            chunks=all_chunks,
            triples=all_triples,
            facts=retrieved_facts,
            summaries=all_summaries,
            edge_triples=edge_triples,
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
                "node_count": len(all_nodes),
                "edge_count": len(edge_triples),
                "chunk_count": len(all_chunks),
                "triple_count": len(all_triples),
                "fact_count": len(retrieved_facts),
                "summary_count": len(all_summaries),
                # Retrieval metadata (thesis-relevant metrics)
                "retrieval_method": "iterative",
                "retrieval_iterations": retrieval_result.iterations_performed,
                "retrieval_query_refinements": len(retrieval_result.refined_queries),
                "retrieval_memories_found": len(retrieval_result.memories),
                "retrieval_scoped_nodes": len(all_nodes),
                "includes_target_description": True,
            },
        )

    def _build_context_with_direct_extraction(
        self,
        scope: EvaluationScope,
        all_nodes: list,
        edge_triples: list[KnowledgeTriple],
    ) -> ContextResult:
        """
        Build context using direct extraction (no retrieval).

        This is the fallback when iterative retrieval is disabled or unavailable.
        """
        all_chunks, all_triples, all_facts, all_summaries = self._load_node_artifacts(
            scope=scope,
            nodes=all_nodes,
            include_chunks=self.include_chunks,
            include_triples=self.llm_provider is not None,
            include_facts=not self.skip_fact_extraction,
            include_summaries=True,
            allow_llm_summaries=not self.skip_summary_extraction,
        )
        # Build context string with all four structures
        context_string = self._build_full_chart_context_string(
            scope=scope,
            nodes=all_nodes,
            chunks=all_chunks,
            triples=all_triples,
            facts=all_facts,
            summaries=all_summaries,
            edge_triples=edge_triples,
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
                "node_count": len(all_nodes),
                "edge_count": len(edge_triples),
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

        with logfire.span(
            "structural_memory.build_context_async",
            target_node=scope.target_node.name,
            chart=scope.chart.name,
        ):
            return await asyncio.to_thread(self.build_context, scope, query)

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
            if self.use_full_chart_context:
                return LayerContext(
                    layer=3,
                    layer_name=get_layer_name(3),
                    content="Full chart context uses no trace layer.",
                    metadata={"full_chart_context": True},
                )
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

    def _build_full_chart_context_string(
        self,
        scope: EvaluationScope,
        nodes: list,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        edge_triples: list[KnowledgeTriple],
        include_chunks: bool = True,
    ) -> str:
        """
        Build a full-chart context string using mixed memory for all nodes.

        Mirrors the full-context strategy structure while swapping in
        mixed structural memory representations.
        """
        sections = []

        if scope.has_project_context:
            domain_layer = self._build_domain_layer(scope)
            sections.append("FULL PROJECT CONTEXT")
            sections.append(domain_layer.content)

        node_lines: list[str] = []
        for node in nodes:
            node_id = str(node.id)
            block = self._format_full_chart_node_memory(
                node.name,
                node_id,
                chunks,
                triples,
                facts,
                summaries,
                include_chunks=include_chunks,
            )
            if block:
                node_lines.append(block)

        sections.append("FULL CHART NODES")
        sections.append("\n".join(node_lines) if node_lines else "No nodes found.")

        edge_lines: list[str] = []
        for triple in edge_triples:
            head = triple.head
            tail = triple.tail
            tail_text = f"{tail}"
            edge_lines.append(f"- ({head}, leads_to, {tail_text})")
        sections.append("FULL CHART EDGES")
        sections.append("\n".join(edge_lines) if edge_lines else "No edges found.")

        return "\n\n".join(sections)

    def _format_full_chart_node_memory(
        self,
        node_name: str,
        node_id: str,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        include_chunks: bool = True,
    ) -> str:
        """Format mixed memory for a node in full-chart mode."""
        node_chunks = [c for c in chunks if c.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        node_facts = [f for f in facts if f.node_id == node_id]
        node_summaries = [s for s in summaries if s.node_id == node_id]

        if not any([node_chunks, node_triples, node_facts, node_summaries]):
            return ""

        lines = [f"- {node_name}"]

        if node_summaries:
            lines.append("  Summary:")
            for s in node_summaries:
                lines.append(f"    {s.content}")

        if node_triples:
            lines.append("  Knowledge Triples:")
            seen = set()
            for t in node_triples:
                t_key = str(t)
                if t_key in seen:
                    continue
                seen.add(t_key)
                lines.append(f"    - {t}")

        if node_facts:
            lines.append("  Atomic Facts:")
            for f in node_facts:
                lines.append(f"    - {f.fact}")

        if include_chunks:
            desc_chunks = [c for c in node_chunks if c.source == "description"]
            if desc_chunks:
                lines.append("  Chunks:")
                for c in desc_chunks[: self.max_chunks_per_node]:
                    content = c.content.replace("\n", "\n    ")
                    lines.append(f"    {content}")

        lines.append("")
        return "\n".join(lines)

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
        if self.use_full_chart_context:
            layers.append(
                LayerContext(
                    layer=3,
                    layer_name=get_layer_name(3),
                    content="Full chart context uses no trace layer.",
                    metadata={"full_chart_context": True},
                )
            )
        else:
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

        def build_mixed_block(
            title: str,
            text: str,
            summary: str,
            facts: list[str],
            triples: list[str],
        ) -> list[str]:
            if not text:
                return []
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
            inventory = ArtifactInventory(
                self.llm_provider,
                allow_llm_summaries=not self.skip_summary_extraction,
            )
            concept_artifacts = []
            pillar_artifacts: dict[str, list[Any]] = {}

            artifact_types: list[str] = []
            if not self.skip_summary_extraction:
                artifact_types.append(ARTIFACT_SUMMARY)
            if not self.skip_fact_extraction:
                artifact_types.append(ARTIFACT_FACTS)
            if self.llm_provider:
                artifact_types.append(ARTIFACT_TRIPLES)

            if scope.game_concept:
                concept_artifacts = inventory.get_or_build_concept_artifacts(
                    concept_id=str(scope.game_concept.id),
                    concept_text=scope.game_concept.content or "",
                    artifact_types=artifact_types,
                    project_id=str(getattr(scope.project, "id", ""))
                    or str(getattr(scope.game_concept, "project_id", "")),
                )

            if scope.project_pillars:
                for pillar in scope.project_pillars:
                    pillar_artifacts[str(pillar.id)] = (
                        inventory.get_or_build_pillar_artifacts(
                            pillar_id=str(pillar.id),
                            pillar_name=getattr(pillar, "name", "") or "Pillar",
                            pillar_description=getattr(pillar, "description", "") or "",
                            artifact_types=artifact_types,
                            project_id=str(getattr(pillar, "project_id", "") or ""),
                        )
                    )

            for title, text in entries:
                summary_text = "N/A"
                facts_list: list[str] = []
                triples_list: list[str] = []

                if title == "Game Concept" and concept_artifacts:
                    for artifact in concept_artifacts:
                        if artifact.artifact_type == ARTIFACT_SUMMARY:
                            summary_text = artifact.content or "N/A"
                        elif artifact.artifact_type == ARTIFACT_FACTS:
                            facts_list = [
                                f.get("fact", "") for f in artifact.content or []
                            ]
                        elif artifact.artifact_type == ARTIFACT_TRIPLES:
                            triples_list = [
                                t.get("text", "") for t in artifact.content or []
                            ]
                else:
                    for pillar in scope.project_pillars or []:
                        pillar_name = getattr(pillar, "name", "") or "Pillar"
                        if title == f"Pillar: {pillar_name}":
                            artifacts = pillar_artifacts.get(str(pillar.id), [])
                            for artifact in artifacts:
                                if artifact.artifact_type == ARTIFACT_SUMMARY:
                                    summary_text = artifact.content or "N/A"
                                elif artifact.artifact_type == ARTIFACT_FACTS:
                                    facts_list = [
                                        f.get("fact", "")
                                        for f in artifact.content or []
                                    ]
                                elif artifact.artifact_type == ARTIFACT_TRIPLES:
                                    triples_list = [
                                        t.get("text", "")
                                        for t in artifact.content or []
                                    ]
                            break

                content_parts.extend(
                    build_mixed_block(
                        title=title,
                        text=text,
                        summary=summary_text,
                        facts=facts_list,
                        triples=triples_list,
                    )
                )

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

    Uses full-chart context and replaces raw descriptions with
    knowledge triples and atomic facts only.
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
            skip_summary_extraction=True,
            **kwargs,
        )

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build simple structural memory context for evaluation.

        Full-chart traversal + triples/facts only (no summaries/chunks).
        """
        containers = scope.chart.containers.select_related("content").all()
        all_nodes = [c.content for c in containers if c.content is not None]
        if scope.target_node not in all_nodes:
            all_nodes.append(scope.target_node)
        edge_triples = self._load_chart_edge_triples(scope.chart)

        cache_key = self._build_context_cache_key(scope, all_nodes)
        cached = self._get_cached_context(cache_key)
        if cached:
            return cached

        _, all_triples, all_facts, all_summaries = self._load_node_artifacts(
            scope=scope,
            nodes=all_nodes,
            include_chunks=False,
            include_triples=self.llm_provider is not None,
            include_facts=not self.skip_fact_extraction,
            include_summaries=False,
            allow_llm_summaries=False,
        )
        context_string = self._build_full_chart_context_string(
            scope=scope,
            nodes=all_nodes,
            chunks=[],
            triples=all_triples,
            facts=all_facts,
            summaries=[],
            edge_triples=edge_triples,
            include_chunks=False,
        )

        layers = self._create_synthetic_layers(
            scope,
            [],
            all_triples,
            all_facts,
            [],
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
                "node_count": len(all_nodes),
                "edge_count": len(edge_triples),
                "chunk_count": 0,
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
                "summary_count": 0,
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

    def _build_domain_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L1 Domain layer with facts/triples only (no summaries/chunks)."""
        content_parts = []

        entries: list[tuple[str, str]] = []
        if scope.game_concept:
            entries.append(("Game Concept", scope.game_concept.content or ""))
        if scope.project_pillars:
            for pillar in scope.project_pillars:
                name = getattr(pillar, "name", "") or "Pillar"
                desc = getattr(pillar, "description", "") or ""
                entries.append((f"Pillar: {name}", desc))

        if entries:
            inventory = ArtifactInventory(self.llm_provider)
            artifact_types: list[str] = []
            if not self.skip_fact_extraction:
                artifact_types.append(ARTIFACT_FACTS)
            if self.llm_provider:
                artifact_types.append(ARTIFACT_TRIPLES)

            concept_artifacts = []
            pillar_artifacts: dict[str, list[Any]] = {}

            if scope.game_concept:
                concept_artifacts = inventory.get_or_build_concept_artifacts(
                    concept_id=str(scope.game_concept.id),
                    concept_text=scope.game_concept.content or "",
                    artifact_types=artifact_types,
                    project_id=str(getattr(scope.project, "id", ""))
                    or str(getattr(scope.game_concept, "project_id", "")),
                )

            if scope.project_pillars:
                for pillar in scope.project_pillars:
                    pillar_artifacts[str(pillar.id)] = (
                        inventory.get_or_build_pillar_artifacts(
                            pillar_id=str(pillar.id),
                            pillar_name=getattr(pillar, "name", "") or "Pillar",
                            pillar_description=getattr(pillar, "description", "") or "",
                            artifact_types=artifact_types,
                            project_id=str(getattr(pillar, "project_id", "") or ""),
                        )
                    )

            for title, _ in entries:
                facts_list: list[str] = []
                triples_list: list[str] = []

                if title == "Game Concept" and concept_artifacts:
                    for artifact in concept_artifacts:
                        if artifact.artifact_type == ARTIFACT_FACTS:
                            facts_list = [
                                f.get("fact", "") for f in artifact.content or []
                            ]
                        elif artifact.artifact_type == ARTIFACT_TRIPLES:
                            triples_list = [
                                t.get("text", "") for t in artifact.content or []
                            ]
                else:
                    for pillar in scope.project_pillars or []:
                        pillar_name = getattr(pillar, "name", "") or "Pillar"
                        if title == f"Pillar: {pillar_name}":
                            artifacts = pillar_artifacts.get(str(pillar.id), [])
                            for artifact in artifacts:
                                if artifact.artifact_type == ARTIFACT_FACTS:
                                    facts_list = [
                                        f.get("fact", "")
                                        for f in artifact.content or []
                                    ]
                                elif artifact.artifact_type == ARTIFACT_TRIPLES:
                                    triples_list = [
                                        t.get("text", "")
                                        for t in artifact.content or []
                                    ]

                lines = [f"{title}:"]
                if triples_list:
                    lines.append("Knowledge Triples:")
                    for t in triples_list[:8]:
                        lines.append(f"- {t}")
                if facts_list:
                    lines.append("Atomic Facts:")
                    for f in facts_list[:10]:
                        lines.append(f"- {f}")
                content_parts.append("\n".join(lines))

        return LayerContext(
            layer=1,
            layer_name=get_layer_name(1),
            content=(
                "\n\n".join(content_parts) if content_parts else "No project context"
            ),
            metadata={"source": "project_config", "mixed_memory": True},
        )

    @property
    def requires_embeddings(self) -> bool:
        """Simple SM does not use vector embeddings."""
        return False
