"""
Hierarchical Graph Strategy.

Implements the user's H-MEM adaptation using deterministic graph traversal
instead of vector similarity for context retrieval.

This strategy:
- Uses the 4-layer hierarchy (Domain, Category, Trace, Episode)
- Enumerates all possible paths to/from target node
- Provides pool of prior/future nodes with explicit path listings
- Structured context for coherence evaluation
"""

import logging
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
    build_category_layer,
    build_domain_layer,
    build_episode_layer,
    build_trace_layer,
)
from pxnodes.llm.context.shared.graph_retrieval import (
    get_backward_paths_to_node,
    get_forward_paths_from_node,
)

logger = logging.getLogger(__name__)

# Context template (no evaluation task - prompts add task-specific instructions).
CONTEXT_TEMPLATE = """### HIERARCHICAL CONTEXT

**1. [L1 DOMAIN: GAME PILLARS & CONCEPT]**
{l1_content}

**2. [L2 CATEGORY: CURRENT ARC]**
{l2_content}

**3. [L3 TRACE: PATH CONTEXT]**
{l3_content}

**4. [L4 EPISODE: TARGET NODE]**
{l4_content}"""


@StrategyRegistry.register(StrategyType.HIERARCHICAL_GRAPH)
class HierarchicalGraphStrategy(BaseContextStrategy):
    """
    Hierarchical Graph strategy using deterministic graph traversal.

    This is the user's adaptation of H-MEM that uses explicit graph
    traversal instead of vector similarity for context retrieval.

    Key features:
    - Uses explicit graph structure instead of embeddings
    - Enumerates ALL possible paths to/from target node
    - Provides pool of prior/future nodes with explicit path listings
    - Deterministic retrieval ensures rigid game logic validation
    """

    strategy_type = StrategyType.HIERARCHICAL_GRAPH

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        max_path_length: int = 20,
        **kwargs: Any,
    ):
        """
        Initialize the Hierarchical Graph strategy.

        Args:
            llm_provider: Optional LLM (not used by this strategy)
            max_path_length: Maximum path length for path enumeration
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.max_path_length = max_path_length

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
        3. Reconstruct L3 (Trace) with ALL paths to/from target
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
        (
            l3_trace,
            backward_nodes,
            forward_nodes,
            backward_paths,
            forward_paths,
        ) = self._build_l3_trace(scope)
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
                "backward_node_count": len(backward_nodes),
                "forward_node_count": len(forward_nodes),
                "backward_path_count": len(backward_paths),
                "forward_path_count": len(forward_paths),
                "backward_paths": self._serialize_paths(backward_paths),
                "forward_paths": self._serialize_paths(forward_paths),
                "max_path_length": self.max_path_length,
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
            layer_ctx, _, _, _, _ = self._build_l3_trace(scope)
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
    ) -> tuple[LayerContext, list, list, list, list]:
        """
        Build L3 Trace layer with all paths to/from target.

        Enumerates ALL possible paths and extracts unique nodes for the pool.

        For coherence checking, we need both:
        - PRIOR nodes pool + paths: To verify prerequisites, story continuity
        - FUTURE nodes pool + paths: To verify target properly sets up what comes next

        Returns:
            Tuple of (LayerContext, backward_nodes, forward_nodes,
                      backward_paths, forward_paths)
        """
        # Get all backward paths (paths leading to target)
        backward_paths = get_backward_paths_to_node(
            scope.target_node,
            scope.chart,
            max_length=self.max_path_length,
            max_paths=None,  # No limit on paths
        )

        # Get all forward paths (paths from target)
        forward_paths = get_forward_paths_from_node(
            scope.target_node,
            scope.chart,
            max_length=self.max_path_length,
            max_paths=None,  # No limit on paths
        )

        # Extract unique nodes from paths for the pool (excluding target)
        backward_nodes = list(
            {
                node
                for path in backward_paths
                for node in path
                if node != scope.target_node
            }
        )
        forward_nodes = list(
            {
                node
                for path in forward_paths
                for node in path
                if node != scope.target_node
            }
        )

        # Build layer context with pools and paths
        layer = build_trace_layer(
            backward_nodes=backward_nodes,
            target_node=scope.target_node,
            forward_nodes=forward_nodes,
            backward_paths=backward_paths,
            forward_paths=forward_paths,
        )

        return layer, backward_nodes, forward_nodes, backward_paths, forward_paths

    def _serialize_paths(self, paths: list[list[Any]]) -> list[list[dict]]:
        """
        Serialize paths to list of dicts for JSON storage in metadata.

        Each node is serialized to {"name": ..., "id": ...} for use by agents.
        """
        serialized = []
        for path in paths:
            serialized_path = []
            for node in path:
                serialized_path.append(
                    {
                        "name": getattr(node, "name", "Unknown"),
                        "id": str(getattr(node, "id", "")),
                    }
                )
            serialized.append(serialized_path)
        return serialized

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
