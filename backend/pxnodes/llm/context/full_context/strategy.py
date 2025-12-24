"""
Full Context Strategy.

Provides unfiltered project and path context for RQ1 comparisons:
- Full Game Concept
- Full Design Pillars
- Full descriptions of all path nodes (backward + forward)
"""

from typing import Any, Optional

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
)
from pxnodes.llm.context.hierarchical_graph.layers import build_domain_layer


@StrategyRegistry.register(StrategyType.FULL_CONTEXT)
class FullContextStrategy(BaseContextStrategy):
    """
    Full Context strategy for RQ1 baselines.

    Uses a raw graph dump for baseline comparisons:
    - Full project context (concept + pillars)
    - All nodes in the chart (name, description, components)
    - All edges in the chart (source -> target)

    This provides a high-noise, low-structure baseline to compare against
    structured context strategies.
    """

    strategy_type = StrategyType.FULL_CONTEXT

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        stop_at_checkpoint: bool = False,
        **kwargs: Any,
    ):
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.stop_at_checkpoint = stop_at_checkpoint

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        l1_domain = build_domain_layer(
            project_pillars=scope.project_pillars,
            game_concept=scope.game_concept,
        )

        containers = scope.chart.containers.select_related("content").all()
        nodes = [c.content for c in containers if getattr(c, "content", None)]
        edges = list(scope.chart.edges.select_related("source__content", "target__content").all())

        node_lines: list[str] = []
        for node in nodes:
            node_lines.append(f"- {node.name}")
            if node.description:
                node_lines.append(f"  Description: {node.description}")
            components = getattr(node, "components", None)
            if components:
                comp_list = components.all() if hasattr(components, "all") else list(components)
                for comp in comp_list:
                    def_name = getattr(getattr(comp, "definition", None), "name", "")
                    value = getattr(comp, "value", "")
                    node_lines.append(f"  {def_name}: {value}")

        edge_lines: list[str] = []
        for edge in edges:
            source_name = (
                getattr(getattr(edge.source, "content", None), "name", "")
                if edge.source
                else ""
            )
            target_name = (
                getattr(getattr(edge.target, "content", None), "name", "")
                if edge.target
                else ""
            )
            if source_name or target_name:
                edge_lines.append(f"- {source_name} -> {target_name}")

        context_string = "\n\n".join(
            [
                "FULL PROJECT CONTEXT",
                l1_domain.content,
                "FULL CHART NODES",
                "\n".join(node_lines) if node_lines else "No nodes found.",
                "FULL CHART EDGES",
                "\n".join(edge_lines) if edge_lines else "No edges found.",
            ]
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain],
            metadata={
                "full_context": True,
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "chart_name": scope.chart.name,
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        )

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        if layer == 1:
            return build_domain_layer(
                project_pillars=scope.project_pillars,
                game_concept=scope.game_concept,
            )
        if layer == 3:
            return LayerContext(
                layer=3,
                layer_name="trace",
                content="Full context uses a raw chart dump, no trace layer.",
            )
        if layer == 2:
            return LayerContext(
                layer=2,
                layer_name="category",
                content="Full context uses a raw chart dump, no category layer.",
            )
        return LayerContext(
            layer=4,
            layer_name="episode",
            content="Target node details are included in the raw chart dump.",
        )
