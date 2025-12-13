"""
Structural Memory Strategy.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
as a BaseContextStrategy.

This strategy:
- Extracts Knowledge Triples (deterministic from components/edges)
- Extracts Atomic Facts (LLM-based from descriptions)
- Uses vector embeddings for retrieval
- Supports iterative retrieval with query refinement
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
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
    extract_atomic_facts,
)
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)


@StrategyRegistry.register(StrategyType.STRUCTURAL_MEMORY)
class StructuralMemoryStrategy(BaseContextStrategy):
    """
    Structural Memory strategy from Zeng et al. (2024).

    Uses Knowledge Triples + Atomic Facts with vector embeddings
    and iterative retrieval for building evaluation context.

    Attributes:
        embedding_model: OpenAI embedding model name
        retrieval_iterations: Number of query refinement iterations
        skip_fact_extraction: Skip LLM-based fact extraction
    """

    strategy_type = StrategyType.STRUCTURAL_MEMORY

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 3,
        skip_fact_extraction: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize the Structural Memory strategy.

        Args:
            llm_provider: LLM for atomic fact extraction and query refinement
            embedding_model: OpenAI embedding model name
            retrieval_iterations: Number of query refinement iterations
            skip_fact_extraction: If True, skip LLM-based fact extraction
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.embedding_model = embedding_model
        self.retrieval_iterations = retrieval_iterations
        self.skip_fact_extraction = skip_fact_extraction

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build structural memory context for evaluation.

        Extracts triples and facts from the target node and its neighbors,
        then formats them for LLM evaluation.

        Args:
            scope: Evaluation scope (target node, chart, project context)
            query: Optional query for retrieval (used for iterative refinement)

        Returns:
            ContextResult with triples, facts, and formatted context
        """
        from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice

        # Get graph slice (neighbors)
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)

        # Extract triples for all nodes
        all_triples: list[KnowledgeTriple] = []
        all_triples.extend(
            extract_all_triples(scope.target_node, scope.chart, include_neighbors=False)
        )
        for node in graph_slice.previous_nodes + graph_slice.next_nodes:
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

        # Extract atomic facts (if LLM available)
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            all_facts.extend(extract_atomic_facts(scope.target_node, self.llm_provider))
            for node in graph_slice.previous_nodes:
                all_facts.extend(extract_atomic_facts(node, self.llm_provider))

        # Build context string
        context_string = self._build_context_string(
            scope, graph_slice, all_triples, all_facts
        )

        # Create synthetic layers for compatibility with hierarchical views
        layers = self._create_synthetic_layers(scope, all_triples, all_facts)

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            triples=all_triples,
            facts=all_facts,
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "previous_count": len(graph_slice.previous_nodes),
                "next_count": len(graph_slice.next_nodes),
                "triple_count": len(all_triples),
                "fact_count": len(all_facts),
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
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
    ) -> str:
        """Build the formatted context string for LLM prompt."""
        sections = []

        # Previous nodes section
        if graph_slice.previous_nodes:
            prev_section = "[PREVIOUS NODES - Context Before Target]\n"
            for node in graph_slice.previous_nodes:
                node_triples = [t for t in triples if t.head == node.name]
                if node_triples:
                    prev_section += f"\n{node.name}:\n"
                    for t in node_triples:
                        prev_section += f"  - {t}\n"
            sections.append(prev_section)

        # Target node section
        target_section = f"[TARGET NODE - {scope.target_node.name}]\n"
        target_triples = [t for t in triples if t.head == scope.target_node.name]
        if target_triples:
            target_section += "\nKnowledge Triples:\n"
            for t in target_triples:
                target_section += f"  - {t}\n"
        if facts:
            target_section += "\nAtomic Facts:\n"
            for f in facts:
                target_section += f"  - {f.fact}\n"
        sections.append(target_section)

        # Computed metrics
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
                node_triples = [t for t in triples if t.head == node.name]
                if node_triples:
                    next_section += f"\n{node.name}:\n"
                    for t in node_triples:
                        next_section += f"  - {t}\n"
            sections.append(next_section)

        return "\n".join(sections)

    def _create_synthetic_layers(
        self,
        scope: EvaluationScope,
        triples: list[KnowledgeTriple],
        facts: list[AtomicFact],
    ) -> list[LayerContext]:
        """Create synthetic hierarchy layers for compatibility."""
        layers = []

        # L1 Domain (if project context available)
        if scope.has_project_context:
            layers.append(self._build_domain_layer(scope))

        # L2 Category (chart level)
        layers.append(self._build_chart_layer(scope))

        # L4 Episode (node level) - skip L3 for structural memory
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
