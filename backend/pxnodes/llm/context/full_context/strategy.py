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
from pxnodes.llm.context.hierarchical_graph.layers import (
    build_domain_layer,
    build_trace_layer,
)
from pxnodes.llm.context.hierarchical_graph.traversal import (
    aggregate_player_state,
    forward_bfs,
    reverse_bfs,
)


@StrategyRegistry.register(StrategyType.FULL_CONTEXT)
class FullContextStrategy(BaseContextStrategy):
    """
    Full Context strategy for RQ1 baselines.

    Uses deterministic traversal to capture full path context but does not
    perform any summarization, embedding retrieval, or routing.
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
        # Project context (full concept + pillars)
        l1_domain = build_domain_layer(
            project_pillars=scope.project_pillars,
            game_concept=scope.game_concept,
        )

        # Full path traversal (backward + forward)
        backward_nodes = reverse_bfs(
            scope.target_node,
            scope.chart,
            max_depth=None,
            stop_at_checkpoint=self.stop_at_checkpoint,
        )
        forward_nodes = forward_bfs(
            scope.target_node,
            scope.chart,
            max_depth=None,
        )
        player_state = aggregate_player_state(backward_nodes)
        l3_trace = build_trace_layer(
            path_nodes=backward_nodes,
            player_state=player_state,
            target_node=scope.target_node,
            forward_nodes=forward_nodes,
        )

        context_string = "\n\n".join(
            [
                "FULL PROJECT CONTEXT",
                l1_domain.content,
                "FULL PATH CONTEXT",
                l3_trace.content,
            ]
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain, l3_trace],
            metadata={
                "full_context": True,
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "chart_name": scope.chart.name,
                "backward_path": [
                    {"id": str(getattr(n, "id", "")), "name": getattr(n, "name", "")}
                    for n in backward_nodes
                ],
                "forward_path": [
                    {"id": str(getattr(n, "id", "")), "name": getattr(n, "name", "")}
                    for n in forward_nodes
                ],
                "backward_path_length": len(backward_nodes),
                "forward_path_length": len(forward_nodes),
                "stop_at_checkpoint": self.stop_at_checkpoint,
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
            backward_nodes = reverse_bfs(
                scope.target_node,
                scope.chart,
                max_depth=None,
                stop_at_checkpoint=self.stop_at_checkpoint,
            )
            forward_nodes = forward_bfs(
                scope.target_node,
                scope.chart,
                max_depth=None,
            )
            player_state = aggregate_player_state(backward_nodes)
            return build_trace_layer(
                path_nodes=backward_nodes,
                player_state=player_state,
                target_node=scope.target_node,
                forward_nodes=forward_nodes,
            )
        if layer == 2:
            return LayerContext(
                layer=2,
                layer_name="category",
                content="No category layer in full context strategy.",
            )
        return LayerContext(
            layer=4,
            layer_name="episode",
            content="Target node details are provided separately in prompts.",
        )
