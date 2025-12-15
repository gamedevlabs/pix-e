"""
Structural Memory Strategy.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
as a BaseContextStrategy.

This strategy extracts four types of memory structures:
- Chunks: Raw text segments (deterministic)
- Knowledge Triples: Structured relationships (deterministic from components/edges)
- Atomic Facts: Indivisible information units (LLM-based from descriptions)
- Summaries: Condensed overviews (LLM-based)

Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries
"""

from typing import Any, Optional

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
)
from pxnodes.llm.context.structural_memory.summaries import (
    Summary,
    create_fallback_summary,
    extract_summary,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)


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

    This provides remarkable resilience in noisy environments and
    balanced performance across diverse tasks.

    Attributes:
        embedding_model: OpenAI embedding model name
        retrieval_iterations: Number of query refinement iterations
        skip_fact_extraction: Skip LLM-based fact extraction
        skip_summary_extraction: Skip LLM-based summary extraction
    """

    strategy_type = StrategyType.STRUCTURAL_MEMORY

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 3,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize the Mixed Structural Memory strategy.

        Args:
            llm_provider: LLM for fact/summary extraction and query refinement
            embedding_model: OpenAI embedding model name
            retrieval_iterations: Number of query refinement iterations
            skip_fact_extraction: If True, skip LLM-based fact extraction
            skip_summary_extraction: If True, skip LLM-based summary extraction
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.embedding_model = embedding_model
        self.retrieval_iterations = retrieval_iterations
        self.skip_fact_extraction = skip_fact_extraction
        self.skip_summary_extraction = skip_summary_extraction

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build mixed structural memory context for evaluation.

        Extracts all four memory structures from Zeng et al. (2024):
        - Chunks: Raw text segments
        - Knowledge Triples: Structured relationships
        - Atomic Facts: Indivisible information units
        - Summaries: Condensed overviews

        Args:
            scope: Evaluation scope (target node, chart, project context)
            query: Optional query for retrieval (used for iterative refinement)

        Returns:
            ContextResult with all four memory structures and formatted context
        """
        from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice

        # Get graph slice (neighbors)
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)
        all_nodes = (
            [scope.target_node] + graph_slice.previous_nodes + graph_slice.next_nodes
        )

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
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            for node in all_nodes:
                all_facts.extend(extract_atomic_facts(node, self.llm_provider))

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
    ) -> list[LayerContext]:
        """
        Create synthetic hierarchy layers for compatibility.

        Maps mixed memory structures to hierarchical layers:
        - L1 Domain: Project context (pillars, game concept)
        - L2 Category: Chart-level context
        - L3 Trace: Neighbor nodes summary
        - L4 Episode: Target node with all four memory types
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
        layers.append(self._build_neighbor_layer(scope))

        # L4 Episode (node level with all memory structures)
        layers.append(self._build_node_layer(scope))

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

    def _build_neighbor_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L3 Trace layer from neighbors."""
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

    def _build_node_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L4 Episode layer from target node."""
        node = scope.target_node
        triples = extract_all_triples(node, scope.chart, include_neighbors=False)

        content_parts = [
            f"Node: {node.name}",
            f"Description: {node.description or 'N/A'}",
            "",
            "Knowledge Triples:",
        ]
        for t in triples[:10]:  # Limit to avoid huge context
            content_parts.append(f"  - {t}")

        return LayerContext(
            layer=4,
            layer_name=get_layer_name(4),
            content="\n".join(content_parts),
            metadata={"node_id": str(node.id), "triple_count": len(triples)},
        )

    @property
    def requires_embeddings(self) -> bool:
        """Structural Memory uses vector embeddings for retrieval."""
        return True

    @property
    def requires_llm(self) -> bool:
        """Requires LLM for atomic fact extraction (unless skipped)."""
        return not self.skip_fact_extraction
