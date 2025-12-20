"""
Structural Memory Strategy.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
as a BaseContextStrategy, with domain-specific adaptations for graph-structured
game design content.

This strategy extracts four types of memory structures:
- Chunks: Raw text segments (deterministic)
- Knowledge Triples: Structured relationships (deterministic from components/edges)
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

import logging
from typing import Any, Optional, cast

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
    get_layer_name,
)
from pxnodes.llm.context.structural_memory.chunks import (
    Chunk,
    extract_chunks,
)
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
    extract_atomic_facts,
    extract_atomic_facts_async,
)
from pxnodes.llm.context.structural_memory.summaries import (
    Summary,
    create_fallback_summary,
    extract_summary,
    extract_summary_async,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
    extract_all_triples_async,
)

logger = logging.getLogger(__name__)


@StrategyRegistry.register(StrategyType.STRUCTURAL_MEMORY)
class StructuralMemoryStrategy(BaseContextStrategy):
    """
    Mixed Structural Memory strategy from Zeng et al. (2024).

    Implements the full mixed memory approach with four structures:
    - Chunks: Raw text segments (deterministic)
    - Knowledge Triples: Structured relationships (deterministic)
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

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 3,
        retrieval_top_k: int = 50,
        use_iterative_retrieval: bool = True,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
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
        from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice

        # ============================================================
        # STAGE 1: Deterministic Graph Scoping (Domain Adaptation)
        # ============================================================
        # Use BFS to identify path-relevant nodes. This constrains the
        # search space for retrieval to only contextually relevant nodes.
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)
        all_nodes = (
            [scope.target_node] + graph_slice.previous_nodes + graph_slice.next_nodes
        )
        scoped_node_ids = [str(n.id) for n in all_nodes]

        logger.info(
            f"Stage 1 (Scoping): Found {len(all_nodes)} path-relevant nodes "
            f"via BFS traversal (depth={scope.depth})"
        )

        # ============================================================
        # STAGE 2: Memory Extraction or Iterative Retrieval
        # ============================================================
        if self.use_iterative_retrieval and self.llm_provider:
            # Use iterative retrieval from Zeng et al. (2024)
            # but SCOPED to path-relevant nodes only
            return self._build_context_with_iterative_retrieval(
                scope, graph_slice, all_nodes, scoped_node_ids, query
            )
        else:
            # Fallback: Direct extraction without retrieval
            return self._build_context_with_direct_extraction(
                scope, graph_slice, all_nodes
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
        (chunks, derived triples, summaries).
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

        # Compute derived triples (these are computed, not stored)
        derived_triples = compute_derived_triples(
            scope.target_node,
            graph_slice.previous_nodes,
            graph_slice.next_nodes,
        )

        # Combine retrieved triples with derived triples
        all_triples = retrieved_triples + derived_triples

        # Extract summaries (or use fallback)
        all_summaries: list[Summary] = []
        if self.llm_provider and not self.skip_summary_extraction:
            for node in all_nodes:
                all_summaries.append(extract_summary(node, self.llm_provider))
        else:
            for node in all_nodes:
                all_summaries.append(create_fallback_summary(node))

        # Build context string
        context_string = self._build_context_string(
            scope, graph_slice, all_chunks, all_triples, retrieved_facts, all_summaries
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
                "derived_triple_count": len(derived_triples),
                # Retrieval metadata (thesis-relevant metrics)
                "retrieval_method": "iterative",
                "retrieval_iterations": retrieval_result.iterations_performed,
                "retrieval_query_refinements": len(retrieval_result.refined_queries),
                "retrieval_memories_found": len(retrieval_result.memories),
                "retrieval_scoped_nodes": len(graph_slice.previous_nodes)
                + len(graph_slice.next_nodes)
                + 1,
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

        # 2. Extract KNOWLEDGE TRIPLES (deterministic - structured relationships)
        all_triples: list[KnowledgeTriple] = []
        for node in all_nodes:
            all_triples.extend(
                extract_all_triples(node, scope.chart, include_neighbors=False)
            )

        # Compute derived triples (intensity deltas, category transitions)
        derived_triples = compute_derived_triples(
            scope.target_node,
            graph_slice.previous_nodes,
            graph_slice.next_nodes,
        )
        all_triples.extend(derived_triples)

        # 3. Extract ATOMIC FACTS (LLM-based - indivisible information units)
        # force_regenerate=True bypasses vector store cache to ensure fresh extraction
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            for node in all_nodes:
                all_facts.extend(
                    extract_atomic_facts(node, self.llm_provider, force_regenerate=True)
                )

        # 4. Extract SUMMARIES (LLM-based - condensed overviews)
        all_summaries: list[Summary] = []
        if self.llm_provider and not self.skip_summary_extraction:
            for node in all_nodes:
                all_summaries.append(extract_summary(node, self.llm_provider))
        else:
            # Use fallback summaries when LLM unavailable
            for node in all_nodes:
                all_summaries.append(create_fallback_summary(node))

        # Build context string with all four structures
        context_string = self._build_context_string(
            scope, graph_slice, all_chunks, all_triples, all_facts, all_summaries
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
                "derived_triple_count": len(derived_triples),
                "retrieval_method": "direct_extraction",
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

        import logfire
        from asgiref.sync import sync_to_async

        from pxnodes.llm.context.shared.graph_retrieval import get_full_path

        with logfire.span(
            "structural_memory.build_context_async",
            target_node=scope.target_node.name,
            chart=scope.chart.name,
        ):
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

            # 2. PARALLEL: Extract knowledge triples + atomic facts for all nodes
            all_triples: list[KnowledgeTriple] = []
            all_facts: list[AtomicFact] = []

            if self.llm_provider and not self.skip_fact_extraction:
                with logfire.span(
                    "extract_knowledge_structures",
                    node_count=len(all_nodes),
                    extraction_types=["knowledge_triples", "atomic_facts"],
                ):
                    # Create parallel tasks for each node
                    triple_tasks = [
                        extract_all_triples_async(node, scope.chart, self.llm_provider)
                        for node in all_nodes
                    ]
                    fact_tasks = [
                        extract_atomic_facts_async(
                            node, self.llm_provider, force_regenerate=True
                        )
                        for node in all_nodes
                    ]

                    # Run all in parallel
                    results = await asyncio.gather(
                        *triple_tasks, *fact_tasks, return_exceptions=True
                    )

                    # Split results
                    triple_results = results[: len(all_nodes)]
                    fact_results = results[len(all_nodes) :]

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

                    logfire.info(
                        "knowledge_structures_extracted",
                        triple_count=len(all_triples),
                        fact_count=len(all_facts),
                    )
            else:
                # Fallback: extract triples only (no LLM)
                for node in all_nodes:
                    triples = await sync_to_async(
                        extract_all_triples, thread_sensitive=True
                    )(node, scope.chart, include_neighbors=False)
                    all_triples.extend(triples)

            # Compute derived triples (intensity deltas, category transitions)
            with logfire.span("compute_derived_triples"):
                derived_triples = await sync_to_async(
                    compute_derived_triples, thread_sensitive=True
                )(
                    scope.target_node,
                    graph_slice.previous_nodes,
                    graph_slice.next_nodes,
                )
                all_triples.extend(derived_triples)
                logfire.info("derived_triples_computed", count=len(derived_triples))

            # 3. PARALLEL: Extract summaries for all nodes
            all_summaries: list[Summary] = []

            if self.llm_provider and not self.skip_summary_extraction:
                with logfire.span(
                    "extract_summaries",
                    node_count=len(all_nodes),
                ):
                    summary_tasks = [
                        extract_summary_async(node, self.llm_provider)
                        for node in all_nodes
                    ]

                    summary_results = await asyncio.gather(
                        *summary_tasks, return_exceptions=True
                    )

                    for result in summary_results:
                        if isinstance(result, Summary):
                            all_summaries.append(result)
                        elif isinstance(result, Exception):
                            logger.warning(f"Summary extraction failed: {result}")

                    logfire.info("summaries_extracted", count=len(all_summaries))
            else:
                # Use fallback summaries when LLM unavailable
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
                    "derived_triple_count": len(derived_triples),
                    "retrieval_method": "async_parallel_extraction",
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

        # Previous nodes section
        if graph_slice.previous_nodes:
            prev_section = "[PREVIOUS NODES - Context Before Target]\n"
            for node in graph_slice.previous_nodes:
                node_id = str(node.id)
                prev_section += self._format_node_memory(
                    node.name, node_id, chunks, triples, facts, summaries
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
        )
        sections.append(target_section)

        # Computed metrics (derived triples)
        derived = [t for t in triples if "delta" in t.relation.lower()]
        if derived:
            metrics_section = "[COMPUTED METRICS]\n"
            for t in derived:
                metrics_section += f"  - {t}\n"
            sections.append(metrics_section)

        # Next nodes section
        if graph_slice.next_nodes:
            next_section = "[NEXT NODES - Context After Target]\n"
            for node in graph_slice.next_nodes:
                node_id = str(node.id)
                next_section += self._format_node_memory(
                    node.name, node_id, chunks, triples, facts, summaries
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
            for t in node_triples:
                lines.append(f"    - {t}")

        # 3. Atomic Facts (indivisible information)
        if node_facts:
            lines.append("\n  Atomic Facts:")
            for f in node_facts:
                lines.append(f"    - {f.fact}")

        # 4. Chunks (raw text - only include description chunks, skip name)
        desc_chunks = [c for c in node_chunks if c.source == "description"]
        if desc_chunks:
            lines.append("\n  Raw Text:")
            for c in desc_chunks:
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
        """Build L1 Domain layer from project context."""
        content_parts = []

        if scope.game_concept:
            content_parts.append(f"Game Concept: {scope.game_concept.content[:500]}")

        if scope.project_pillars:
            pillars_text = "; ".join(
                f"{p.name}: {p.description[:100]}" for p in scope.project_pillars[:3]
            )
            content_parts.append(f"Design Pillars: {pillars_text}")

        return LayerContext(
            layer=1,
            layer_name=get_layer_name(1),
            content="\n".join(content_parts) if content_parts else "No project context",
            metadata={"source": "project_config"},
        )

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
            node_triples = extract_all_triples(
                node, scope.chart, include_neighbors=False
            )
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
