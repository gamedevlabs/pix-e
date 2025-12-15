"""
Combined Strategy Implementation.

Combines Mixed Structural Memory (Zeng et al. 2024) data representation with
H-MEM (Sun & Zeng 2025) hierarchical organization.

This strategy uses all four memory structures from Zeng et al. (2024):
- Chunks: Raw text segments
- Knowledge Triples: Structured relationships
- Atomic Facts: Indivisible information units
- Summaries: Condensed overviews

Organized using H-MEM's 4-layer hierarchy:
- L1 Domain: Project-level context
- L2 Category: Chart-level context
- L3 Trace: Path/neighbor context
- L4 Episode: Target node context

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
from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice
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

# Combined context template with all four memory structures
COMBINED_CONTEXT_TEMPLATE = """### COMBINED HIERARCHICAL + MIXED MEMORY CONTEXT

**[L1 DOMAIN - Project Level]**
{l1_content}

**[L2 CATEGORY - Chart Level]**
{l2_content}

**[L3 TRACE - Path Level]**
{l3_content}

**[L4 EPISODE - Target Node]**

Summary:
{l4_summary}

Knowledge Triples:
{l4_triples}

Atomic Facts:
{l4_facts}

Raw Text:
{l4_chunks}

**[COMPUTED METRICS]**
{derived_triples}
"""


@StrategyRegistry.register(StrategyType.COMBINED)
class CombinedStrategy(BaseContextStrategy):
    """
    Combined strategy using Mixed Structural Memory + H-MEM organization.

    This hybrid approach combines:

    1. Mixed Structural Memory (Zeng et al. 2024) - all four structures:
       - Chunks: Raw text segments (deterministic)
       - Knowledge Triples: Structured relationships (deterministic)
       - Atomic Facts: Indivisible information units (LLM-based)
       - Summaries: Condensed overviews (LLM-based)

    2. H-MEM (Sun & Zeng 2025) hierarchical organization:
       - L1 Domain: Project-level context (pillars, game concept)
       - L2 Category: Chart-level context
       - L3 Trace: Path/neighbor context with structural data
       - L4 Episode: Target node with all four memory structures

    Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries

    This allows thesis comparison of:
    - Pure structural approach (StructuralMemoryStrategy)
    - Pure hierarchical approach (HierarchicalGraphStrategy)
    - Pure embedding approach (HMEMStrategy)
    - Combined approach (this strategy)
    """

    strategy_type = StrategyType.COMBINED

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        skip_fact_extraction: bool = False,
        skip_summary_extraction: bool = False,
        include_derived_triples: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the Combined strategy.

        Args:
            llm_provider: LLM for fact/summary extraction
            skip_fact_extraction: Skip LLM-based fact extraction
            skip_summary_extraction: Skip LLM-based summary extraction
            include_derived_triples: Include computed metrics (intensity deltas)
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.skip_fact_extraction = skip_fact_extraction
        self.skip_summary_extraction = skip_summary_extraction
        self.include_derived_triples = include_derived_triples

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build combined context using all four memory structures + hierarchy.

        Extracts all four memory structures from Zeng et al. (2024):
        - Chunks: Raw text segments
        - Knowledge Triples: Structured relationships
        - Atomic Facts: Indivisible information units
        - Summaries: Condensed overviews

        Organized in H-MEM 4-layer hierarchy:
        - L1 Domain: Project context
        - L2 Category: Chart context
        - L3 Trace: Path nodes with mixed memory
        - L4 Episode: Target node with all four structures

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional query (not used in combined approach)

        Returns:
            ContextResult with all four memory structures in hierarchical format
        """
        # Get graph slice for path context
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)
        all_nodes = (
            [scope.target_node] + graph_slice.previous_nodes + graph_slice.next_nodes
        )

        # Build hierarchical layers (L1-L2 from H-MEM style)
        l1_domain = self._build_domain_layer(scope)
        l2_category = self._build_category_layer(scope)

        # 1. Extract CHUNKS (deterministic - raw text segments)
        all_chunks: list[Chunk] = []
        for node in all_nodes:
            all_chunks.extend(extract_chunks(node))

        # 2. Extract KNOWLEDGE TRIPLES (deterministic)
        all_triples: list[KnowledgeTriple] = []
        for node in all_nodes:
            all_triples.extend(
                extract_all_triples(node, scope.chart, include_neighbors=False)
            )

        # Compute derived triples (intensity deltas, transitions)
        derived_triples: list[KnowledgeTriple] = []
        if self.include_derived_triples:
            derived_triples = compute_derived_triples(
                scope.target_node,
                graph_slice.previous_nodes,
                graph_slice.next_nodes,
            )
        all_triples.extend(derived_triples)

        # 3. Extract ATOMIC FACTS (LLM-based)
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            for node in all_nodes:
                all_facts.extend(extract_atomic_facts(node, self.llm_provider))

        # 4. Extract SUMMARIES (LLM-based)
        all_summaries: list[Summary] = []
        if self.llm_provider and not self.skip_summary_extraction:
            for node in all_nodes:
                all_summaries.append(extract_summary(node, self.llm_provider))
        else:
            for node in all_nodes:
                all_summaries.append(create_fallback_summary(node))

        # Build L3 with path context
        l3_trace = self._build_trace_layer_with_mixed_memory(
            scope, graph_slice, all_chunks, all_triples, all_facts, all_summaries
        )

        # Build L4 with all four structures for target node
        l4_episode = self._build_episode_layer_with_mixed_memory(
            scope, all_chunks, all_triples, all_facts, all_summaries
        )

        # Format context string
        context_string = self._format_context(
            l1_domain,
            l2_category,
            l3_trace,
            scope,
            all_chunks,
            all_triples,
            all_facts,
            all_summaries,
            derived_triples,
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain, l2_category, l3_trace, l4_episode],
            chunks=all_chunks,
            triples=all_triples,
            facts=all_facts,
            summaries=all_summaries,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "chunk_count": len(all_chunks),
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
                "summary_count": len(all_summaries),
                "derived_triple_count": len(derived_triples),
                "previous_nodes": len(graph_slice.previous_nodes),
                "next_nodes": len(graph_slice.next_nodes),
            },
        )

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """Get context for a specific layer."""
        if layer == 1:
            return self._build_domain_layer(scope)
        elif layer == 2:
            return self._build_category_layer(scope)
        elif layer == 3:
            # Build full context to get L3
            result = self.build_context(scope)
            return (
                result.layers[2]
                if len(result.layers) > 2
                else LayerContext(
                    layer=3, layer_name="trace", content="No path context"
                )
            )
        else:  # layer == 4
            result = self.build_context(scope)
            return (
                result.layers[3]
                if len(result.layers) > 3
                else LayerContext(
                    layer=4, layer_name="episode", content="No episode context"
                )
            )

    def _build_domain_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L1 Domain layer from project context."""
        content_parts = []

        if scope.game_concept:
            concept = getattr(scope.game_concept, "content", "")
            if concept:
                content_parts.append(f"Game Concept: {concept[:800]}")

        if scope.project_pillars:
            pillar_texts = []
            for p in scope.project_pillars[:5]:
                name = getattr(p, "name", "")
                desc = getattr(p, "description", "")[:150]
                pillar_texts.append(f"- {name}: {desc}")
            content_parts.append("Design Pillars:\n" + "\n".join(pillar_texts))

        return LayerContext(
            layer=1,
            layer_name=get_layer_name(1),
            content=(
                "\n\n".join(content_parts) if content_parts else "No project context"
            ),
            metadata={"source": "combined_l1"},
        )

    def _build_category_layer(self, scope: EvaluationScope) -> LayerContext:
        """Build L2 Category layer from chart."""
        chart = scope.chart
        content = f"Chart: {chart.name}\nDescription: {chart.description or 'N/A'}"

        return LayerContext(
            layer=2,
            layer_name=get_layer_name(2),
            content=content,
            metadata={"chart_id": str(chart.id), "source": "combined_l2"},
        )

    def _build_trace_layer_with_mixed_memory(
        self,
        scope: EvaluationScope,
        graph_slice: Any,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
    ) -> LayerContext:
        """Build L3 Trace layer with mixed memory from path nodes."""
        content_parts = []

        # Build path sequence
        if graph_slice.previous_nodes:
            path_names = [n.name for n in graph_slice.previous_nodes]
            content_parts.append(f"Path: {' -> '.join(path_names)} -> [TARGET]")

            # Format each previous node with mixed memory
            for node in graph_slice.previous_nodes:
                node_content = self._format_node_mixed_memory(
                    node.name, str(node.id), chunks, triples, facts, summaries
                )
                if node_content:
                    content_parts.append(node_content)

        # Add next nodes if any
        if graph_slice.next_nodes:
            next_names = [n.name for n in graph_slice.next_nodes]
            content_parts.append(f"\nNext: [TARGET] -> {' -> '.join(next_names)}")

            for node in graph_slice.next_nodes:
                node_content = self._format_node_mixed_memory(
                    node.name, str(node.id), chunks, triples, facts, summaries
                )
                if node_content:
                    content_parts.append(node_content)

        return LayerContext(
            layer=3,
            layer_name=get_layer_name(3),
            content="\n".join(content_parts) if content_parts else "Start of path",
            metadata={
                "previous_count": len(graph_slice.previous_nodes),
                "next_count": len(graph_slice.next_nodes),
                "source": "combined_l3",
            },
        )

    def _build_episode_layer_with_mixed_memory(
        self,
        scope: EvaluationScope,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
    ) -> LayerContext:
        """Build L4 Episode layer with all four memory structures."""
        node = scope.target_node
        node_id = str(node.id)
        node_name = node.name

        content_parts = [f"Target Node: {node_name}"]

        # Filter for target node
        node_summaries = [s for s in summaries if s.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        node_facts = [f for f in facts if f.node_id == node_id]
        node_chunks = [c for c in chunks if c.node_id == node_id]

        # 1. Summary
        if node_summaries:
            content_parts.append("\nSummary:")
            for s in node_summaries:
                content_parts.append(f"  {s.content}")

        # 2. Knowledge Triples
        if node_triples:
            content_parts.append("\nKnowledge Triples:")
            for t in node_triples[:20]:
                content_parts.append(f"  - {t}")

        # 3. Atomic Facts
        if node_facts:
            content_parts.append("\nAtomic Facts:")
            for f in node_facts[:15]:
                content_parts.append(f"  - {f.fact}")

        # 4. Raw Text (description chunks only)
        desc_chunks = [c for c in node_chunks if c.source == "description"]
        if desc_chunks:
            content_parts.append("\nRaw Text:")
            for c in desc_chunks:
                content_parts.append(f"  {c.content}")

        return LayerContext(
            layer=4,
            layer_name=get_layer_name(4),
            content="\n".join(content_parts),
            metadata={
                "node_id": node_id,
                "summary_count": len(node_summaries),
                "triples_count": len(node_triples),
                "facts_count": len(node_facts),
                "chunks_count": len(node_chunks),
                "source": "combined_l4",
            },
        )

    def _format_node_mixed_memory(
        self,
        node_name: str,
        node_id: str,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
    ) -> str:
        """Format all four memory structures for a single node."""
        # Filter for this node
        node_summaries = [s for s in summaries if s.node_id == node_id]
        node_triples = [t for t in triples if t.head == node_name]
        node_facts = [f for f in facts if f.node_id == node_id]

        if not any([node_summaries, node_triples, node_facts]):
            return ""

        lines = [f"\n{node_name}:"]

        # Summary (brief)
        if node_summaries:
            lines.append(f"  Summary: {node_summaries[0].content[:200]}...")

        # Triples (limited)
        if node_triples:
            lines.append("  Triples:")
            for t in node_triples[:5]:
                lines.append(f"    - {t}")

        # Facts (limited)
        if node_facts:
            lines.append("  Facts:")
            for f in node_facts[:5]:
                lines.append(f"    - {f.fact}")

        return "\n".join(lines)

    def _format_context(
        self,
        l1: LayerContext,
        l2: LayerContext,
        l3: LayerContext,
        scope: EvaluationScope,
        chunks: list[Chunk],
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
        summaries: list[Summary],
        derived_triples: list[KnowledgeTriple],
    ) -> str:
        """Format all components into combined context string."""
        target_id = str(scope.target_node.id)
        target_name = scope.target_node.name

        # Filter for target node
        target_summaries = [s for s in summaries if s.node_id == target_id]
        target_triples = [t for t in triples if t.head == target_name]
        target_facts = [f for f in facts if f.node_id == target_id]
        target_chunks = [c for c in chunks if c.node_id == target_id]

        # Format L4 sections
        l4_summary_str = (
            target_summaries[0].content if target_summaries else "(no summary)"
        )

        l4_triples_str = (
            "\n".join(f"  - {t}" for t in target_triples[:20])
            if target_triples
            else "  (none)"
        )

        l4_facts_str = (
            "\n".join(f"  - {f.fact}" for f in target_facts[:15])
            if target_facts
            else "  (none)"
        )

        desc_chunks = [c for c in target_chunks if c.source == "description"]
        l4_chunks_str = (
            "\n".join(f"  {c.content}" for c in desc_chunks)
            if desc_chunks
            else "  (none)"
        )

        derived_str = (
            "\n".join(f"  - {t}" for t in derived_triples[:10])
            if derived_triples
            else "  (none)"
        )

        return COMBINED_CONTEXT_TEMPLATE.format(
            l1_content=l1.content,
            l2_content=l2.content,
            l3_content=l3.content,
            l4_summary=l4_summary_str,
            l4_triples=l4_triples_str,
            l4_facts=l4_facts_str,
            l4_chunks=l4_chunks_str,
            derived_triples=derived_str,
        )

    @property
    def requires_embeddings(self) -> bool:
        """Combined uses structural data, not necessarily embeddings."""
        return False

    @property
    def requires_llm(self) -> bool:
        """Requires LLM for atomic fact extraction (unless skipped)."""
        return not self.skip_fact_extraction
