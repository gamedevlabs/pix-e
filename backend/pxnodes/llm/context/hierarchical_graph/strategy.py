"""
Hierarchical Graph Strategy.

Implements the user's H-MEM adaptation using deterministic graph traversal
instead of vector similarity for context retrieval.

This strategy:
- Uses the 4-layer hierarchy (Domain, Category, Trace, Episode)
- Performs BFS/DFS graph traversal for trace reconstruction
- Aggregates player state (items, mechanics, narrative) along paths
- Provides structured context for coherence evaluation
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
    PlayerState,
    build_category_layer,
    build_domain_layer,
    build_episode_layer,
    build_trace_layer,
)
from pxnodes.llm.context.hierarchical_graph.traversal import (
    aggregate_player_state,
    forward_bfs,
    reverse_bfs,
)

# Context template (no evaluation task - prompts add task-specific instructions).
CONTEXT_TEMPLATE = """### HIERARCHICAL CONTEXT

**1. [L1 DOMAIN: GAME PILLARS & CONCEPT]**
{l1_content}

**2. [L2 CATEGORY: CURRENT ARC]**
{l2_content}

**3. [L3 TRACE: PLAYER STATE]**
{l3_content}

**4. [L4 EPISODE: TARGET NODE]**
{l4_content}"""


@StrategyRegistry.register(StrategyType.HIERARCHICAL_GRAPH)
class HierarchicalGraphStrategy(BaseContextStrategy):
    """
    Hierarchical Graph strategy using deterministic graph traversal.

    This is the user's adaptation of H-MEM that uses BFS/DFS graph
    traversal instead of vector similarity for context retrieval.

    Key differences from H-MEM:
    - Uses explicit graph structure instead of embeddings
    - Deterministic retrieval ensures rigid game logic validation
    - State aggregation tracks items, mechanics, narrative along paths
    """

    strategy_type = StrategyType.HIERARCHICAL_GRAPH

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        max_trace_depth: Optional[int] = None,
        stop_at_checkpoint: bool = True,
        lookahead_depth: int = 1,
        **kwargs: Any,
    ):
        """
        Initialize the Hierarchical Graph strategy.

        Args:
            llm_provider: Optional LLM for summary generation
            max_trace_depth: Max nodes to traverse backward (None = unlimited)
            stop_at_checkpoint: Stop backward traversal at checkpoints
            lookahead_depth: How many successor nodes to include
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.max_trace_depth = max_trace_depth
        self.stop_at_checkpoint = stop_at_checkpoint
        self.lookahead_depth = lookahead_depth

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build hierarchical context using graph traversal.

        Steps:
        1. Retrieve L1 (Domain) from project config - FULL content
        2. Retrieve L2 (Category) from parent chart
        3. Reconstruct L3 (Trace) via BFS - BOTH backward and forward paths
        4. Retrieve L4 (Episode) from target node

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional query (not used in graph traversal)

        Returns:
            ContextResult with 4-layer hierarchical context
        """
        # Build all 4 layers
        l1_domain = self._build_l1_domain(scope)
        l2_category = self._build_l2_category(scope)
        l3_trace, player_state, backward_nodes, forward_nodes = self._build_l3_trace(
            scope
        )
        l4_episode = self._build_l4_episode(scope)

        # Build structured context string
        context_string = self._format_context(
            l1_domain, l2_category, l3_trace, l4_episode
        )

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=[l1_domain, l2_category, l3_trace, l4_episode],
            triples=[],  # Graph strategy doesn't use triples
            facts=[],  # Graph strategy doesn't use facts
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "chart_name": scope.chart.name,
                "backward_path_length": len(backward_nodes),
                "forward_path_length": len(forward_nodes),
                "player_state": player_state.to_dict(),
                "max_trace_depth": self.max_trace_depth,
                "stop_at_checkpoint": self.stop_at_checkpoint,
                "includes_target_description": True,
            },
        )

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """Get context for a specific layer."""
        if layer == 1:
            return self._build_l1_domain(scope)
        elif layer == 2:
            return self._build_l2_category(scope)
        elif layer == 3:
            layer_ctx, _, _, _ = self._build_l3_trace(scope)
            return layer_ctx
        else:  # layer == 4
            return self._build_l4_episode(scope)

    def _build_l1_domain(self, scope: EvaluationScope) -> LayerContext:
        """Build L1 Domain layer from project context."""
        return build_domain_layer(
            project_pillars=scope.project_pillars,
            game_concept=scope.game_concept,
        )

    def _build_l2_category(self, scope: EvaluationScope) -> LayerContext:
        """Build L2 Category layer from chart."""
        return build_category_layer(scope.chart)

    def _build_l3_trace(
        self, scope: EvaluationScope
    ) -> tuple[LayerContext, PlayerState, list, list]:
        """
        Build L3 Trace layer via BFS traversal (backward AND forward).

        For coherence checking, we need both:
        - PREVIOUS nodes: To verify prerequisites, story continuity
        - FUTURE nodes: To verify target properly sets up what comes next

        Returns:
            Tuple of (LayerContext, PlayerState, backward_nodes, forward_nodes)
        """
        # Perform reverse BFS to get backward path (full path to start)
        backward_nodes = reverse_bfs(
            scope.target_node,
            scope.chart,
            max_depth=self.max_trace_depth,
            stop_at_checkpoint=self.stop_at_checkpoint,
        )

        # Perform forward BFS to get forward path (full path to end)
        # Use None for max_depth to get complete forward path
        forward_nodes = forward_bfs(
            scope.target_node,
            scope.chart,
            max_depth=None,  # Get complete forward path
        )

        if not backward_nodes and not forward_nodes:
            from pxnodes.llm.context.shared.graph_retrieval import get_full_path

            graph_slice = get_full_path(scope.target_node, scope.chart)
            backward_nodes = graph_slice.previous_nodes
            forward_nodes = graph_slice.next_nodes

        # Aggregate player state along backward path
        player_state = aggregate_player_state(backward_nodes, self.llm_provider)

        # Build layer context with BOTH backward and forward paths
        layer = build_trace_layer(
            backward_nodes,
            player_state,
            scope.target_node,
            forward_nodes=forward_nodes,
        )

        return layer, player_state, backward_nodes, forward_nodes

    def _build_l4_episode(self, scope: EvaluationScope) -> LayerContext:
        """Build L4 Episode layer from target node."""
        return build_episode_layer(scope.target_node)

    def _format_context(
        self,
        l1: LayerContext,
        l2: LayerContext,
        l3: LayerContext,
        l4: LayerContext,
    ) -> str:
        """Format all layers into evaluation prompt."""
        return CONTEXT_TEMPLATE.format(
            l1_content=l1.content,
            l2_content=l2.content,
            l3_content=l3.content,
            l4_content=l4.content,
        )

    @property
    def requires_embeddings(self) -> bool:
        """Hierarchical Graph uses graph traversal, not embeddings."""
        return False

    @property
    def requires_llm(self) -> bool:
        """LLM is optional (for summary generation only)."""
        return False
