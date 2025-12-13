"""
Combined Strategy Implementation.

Combines Structural Memory (Zeng et al. 2024) data representation with
H-MEM (Sun & Zeng 2025) hierarchical organization.

This strategy:
- Uses Knowledge Triples and Atomic Facts for data representation
- Organizes context using H-MEM's 4-layer hierarchy
- Embeds structured data instead of raw text
- Provides the best of both approaches for thesis comparison
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
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
    extract_atomic_facts,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)

# Combined context template
COMBINED_CONTEXT_TEMPLATE = """### COMBINED HIERARCHICAL + STRUCTURAL CONTEXT

**[L1 DOMAIN - Project Level]**
{l1_content}

**[L2 CATEGORY - Chart Level]**
{l2_content}

**[L3 TRACE - Path Level]**
Knowledge Triples (Path Context):
{l3_triples}

**[L4 EPISODE - Target Node]**
Knowledge Triples:
{l4_triples}

Atomic Facts:
{l4_facts}

Derived Metrics:
{derived_triples}

### EVALUATION
Evaluate the target node's coherence using both the hierarchical context
(L1-L3) and the structural data (triples and facts at L4)."""


@StrategyRegistry.register(StrategyType.COMBINED)
class CombinedStrategy(BaseContextStrategy):
    """
    Combined strategy using Structural Memory + H-MEM organization.

    This hybrid approach:
    1. Uses Structural Memory (Zeng et al. 2024) for data representation:
       - Knowledge Triples for structured relationships
       - Atomic Facts for fine-grained details

    2. Uses H-MEM (Sun & Zeng 2025) for context organization:
       - 4-layer hierarchy (Domain, Category, Trace, Episode)
       - Hierarchical context building

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
        include_derived_triples: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the Combined strategy.

        Args:
            llm_provider: LLM for atomic fact extraction
            skip_fact_extraction: Skip LLM-based fact extraction
            include_derived_triples: Include computed metrics (intensity deltas)
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.skip_fact_extraction = skip_fact_extraction
        self.include_derived_triples = include_derived_triples

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build combined context using structural data + hierarchical organization.

        Steps:
        1. Build H-MEM hierarchical layers (L1-L3)
        2. Extract structural memory data (triples, facts) at L4
        3. Compute derived triples for metrics
        4. Combine into unified context string

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional query (not used in combined approach)

        Returns:
            ContextResult with hierarchical context and structural data
        """
        # Get graph slice for path context
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)

        # Build hierarchical layers (L1-L2 from H-MEM style)
        l1_domain = self._build_domain_layer(scope)
        l2_category = self._build_category_layer(scope)

        # Build L3 with triples from path nodes
        l3_trace, path_triples = self._build_trace_layer_with_triples(
            scope, graph_slice
        )

        # Extract structural data at L4 (target node)
        target_triples = extract_all_triples(
            scope.target_node, scope.chart, include_neighbors=False
        )

        # Extract atomic facts if LLM available
        target_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            target_facts = extract_atomic_facts(scope.target_node, self.llm_provider)

        # Compute derived triples (intensity deltas, transitions)
        derived_triples: list[KnowledgeTriple] = []
        if self.include_derived_triples:
            derived_triples = compute_derived_triples(
                scope.target_node,
                graph_slice.previous_nodes,
                graph_slice.next_nodes,
            )

        # Build L4 layer
        l4_episode = self._build_episode_layer_with_structural(
            scope, target_triples, target_facts
        )

        # Combine all triples and facts
        all_triples = path_triples + target_triples + derived_triples
        all_facts = target_facts

        # Format context string
        context_string = self._format_context(
            l1_domain,
            l2_category,
            l3_trace,
            target_triples,
            target_facts,
            derived_triples,
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain, l2_category, l3_trace, l4_episode],
            triples=all_triples,
            facts=all_facts,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "path_triples_count": len(path_triples),
                "target_triples_count": len(target_triples),
                "derived_triples_count": len(derived_triples),
                "facts_count": len(target_facts),
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
            graph_slice = get_graph_slice(
                scope.target_node, scope.chart, depth=scope.depth
            )
            result = self._build_trace_layer_with_triples(scope, graph_slice)
            return result[0]
        else:  # layer == 4
            triples = extract_all_triples(
                scope.target_node, scope.chart, include_neighbors=False
            )
            facts: list[AtomicFact] = []
            if self.llm_provider and not self.skip_fact_extraction:
                facts = extract_atomic_facts(scope.target_node, self.llm_provider)
            return self._build_episode_layer_with_structural(scope, triples, facts)

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

    def _build_trace_layer_with_triples(
        self,
        scope: EvaluationScope,
        graph_slice: Any,
    ) -> tuple[LayerContext, list[KnowledgeTriple]]:
        """Build L3 Trace layer with triples from path nodes."""
        path_triples: list[KnowledgeTriple] = []
        content_parts = []

        # Build path sequence
        if graph_slice.previous_nodes:
            path_names = [n.name for n in graph_slice.previous_nodes]
            content_parts.append(f"Path: {' -> '.join(path_names)}")

            # Extract triples from path nodes
            for node in graph_slice.previous_nodes:
                node_triples = extract_all_triples(
                    node, scope.chart, include_neighbors=False
                )
                path_triples.extend(node_triples)

        # Format path triples
        if path_triples:
            triple_strs = [str(t) for t in path_triples[:15]]  # Limit
            content_parts.append("Path Triples:\n" + "\n".join(triple_strs))

        layer = LayerContext(
            layer=3,
            layer_name=get_layer_name(3),
            content="\n\n".join(content_parts) if content_parts else "Start of path",
            metadata={
                "path_length": len(graph_slice.previous_nodes),
                "path_triples": len(path_triples),
                "source": "combined_l3",
            },
        )

        return layer, path_triples

    def _build_episode_layer_with_structural(
        self,
        scope: EvaluationScope,
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
    ) -> LayerContext:
        """Build L4 Episode layer with structural data."""
        node = scope.target_node
        content_parts = [
            f"Node: {node.name}",
            f"Description: {node.description or 'N/A'}",
        ]

        # Add triples
        if triples:
            content_parts.append("\nKnowledge Triples:")
            for t in triples[:20]:
                content_parts.append(f"  {t}")

        # Add facts
        if facts:
            content_parts.append("\nAtomic Facts:")
            for f in facts[:10]:
                content_parts.append(f"  - {f.fact}")

        return LayerContext(
            layer=4,
            layer_name=get_layer_name(4),
            content="\n".join(content_parts),
            metadata={
                "node_id": str(node.id),
                "triples_count": len(triples),
                "facts_count": len(facts),
                "source": "combined_l4",
            },
        )

    def _format_context(
        self,
        l1: LayerContext,
        l2: LayerContext,
        l3: LayerContext,
        target_triples: list[KnowledgeTriple],
        target_facts: list[AtomicFact],
        derived_triples: list[KnowledgeTriple],
    ) -> str:
        """Format all components into combined context string."""
        # Format triples and facts
        l4_triples_str = (
            "\n".join(f"  {t}" for t in target_triples[:20])
            if target_triples
            else "  (none)"
        )

        l4_facts_str = (
            "\n".join(f"  - {f.fact}" for f in target_facts[:10])
            if target_facts
            else "  (none)"
        )

        derived_str = (
            "\n".join(f"  {t}" for t in derived_triples[:10])
            if derived_triples
            else "  (none)"
        )

        # Get L3 triples from layer metadata or content
        l3_triples_content = l3.content

        return COMBINED_CONTEXT_TEMPLATE.format(
            l1_content=l1.content,
            l2_content=l2.content,
            l3_triples=l3_triples_content,
            l4_triples=l4_triples_str,
            l4_facts=l4_facts_str,
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
