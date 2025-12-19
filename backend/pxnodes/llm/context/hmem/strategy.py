"""
H-MEM Strategy Implementation.

Implements the faithful H-MEM approach from Sun & Zeng (2025) using
vector embeddings with hierarchical top-down routing.

Key features (from paper):
- Vector embeddings for semantic similarity matching
- Positional index encoding with parent-child pointers for routing
- Hierarchical top-down routing: L1 results constrain L2 search, etc.
- L3 Memory Trace contains path SUMMARIES (not just node names)

Key differences from Hierarchical Graph:
- Uses vector similarity instead of graph traversal
- Stores embeddings for each layer in Django model
- Parent-child pointer routing for efficient retrieval
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
    get_layer_name,
)
from pxnodes.llm.context.hmem.retriever import (
    HMEMContextResult,
    HMEMRetriever,
    compute_path_hash,
)
from pxnodes.llm.context.shared.graph_retrieval import get_all_paths_through_node
from pxnodes.models import HMEMLayerEmbedding

logger = logging.getLogger(__name__)

# H-MEM context template (no similarity scores - they're internal metadata)
HMEM_CONTEXT_TEMPLATE = """### HIERARCHICAL MEMORY CONTEXT (H-MEM)

**[L1 DOMAIN - Project Level]**
{l1_content}

**[L2 CATEGORY - Chart Level]**
{l2_content}

**[L3 TRACE - Path Level]**
{l3_content}

**[L4 EPISODE - Node Level]**
{l4_content}

### EVALUATION
Based on the hierarchical context above, evaluate whether the target node
(L4) is coherent with its surrounding context at all levels."""


@StrategyRegistry.register(StrategyType.HMEM)
class HMEMStrategy(BaseContextStrategy):
    """
    H-MEM strategy using vector embeddings and hierarchical routing.

    This is the faithful implementation of Sun & Zeng (2025) "H-MEM:
    Hierarchical Memory for High-Efficiency Long-Term Reasoning".

    Key implementation details:
    - Hierarchical top-down routing: parent results constrain child search
    - Parent-child pointer links for efficient routing
    - L3 Memory Trace contains path SUMMARIES (paper: "keyword summaries")
    - Similarity scores kept in metadata, NOT shown in output

    Unlike HierarchicalGraphStrategy which uses deterministic graph
    traversal, this strategy uses:
    - Vector embeddings for semantic similarity matching
    - Positional index encoding for hierarchical routing
    - Django model storage for persistent embeddings
    """

    strategy_type = StrategyType.HMEM

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        top_k_per_layer: int = 3,
        auto_embed: bool = True,
        **kwargs: Any,
    ):
        """
        Initialize the H-MEM strategy.

        Args:
            llm_provider: Optional LLM for content summarization
            embedding_model: OpenAI embedding model name
            top_k_per_layer: Number of results to retrieve per layer
            auto_embed: Whether to auto-embed missing content
        """
        super().__init__(llm_provider=llm_provider, **kwargs)
        self.embedding_model = embedding_model
        self.top_k_per_layer = top_k_per_layer
        self.auto_embed = auto_embed
        self.retriever = HMEMRetriever(embedding_model=embedding_model)

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build hierarchical context using H-MEM vector retrieval.

        Steps:
        1. Ensure embeddings exist for the scope (auto-embed if needed)
        2. Build query from target node
        3. Retrieve using hierarchical top-down routing
        4. Format into hierarchical context string (no scores)

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional custom query (defaults to node description)

        Returns:
            ContextResult with H-MEM hierarchical context
        """
        # Build query from node if not provided
        if not query:
            query = self._build_query_from_node(scope.target_node)

        # Auto-embed if needed (with parent-child links)
        if self.auto_embed:
            self._ensure_embeddings(scope)

        # Get project ID
        project_id = self._get_project_id(scope)

        # Retrieve from H-MEM using hierarchical routing
        retrieval_result = self.retriever.retrieve(
            query=query,
            project_id=project_id,
            chart_id=str(scope.chart.id),
            node_id=str(scope.target_node.id),
            top_k_per_layer=self.top_k_per_layer,
        )

        # Build layer contexts (without scores in content)
        layers = self._build_layer_contexts(scope, retrieval_result)

        # Format context string
        context_string = self._format_context(layers)

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            triples=[],  # H-MEM doesn't use triples
            facts=[],  # H-MEM doesn't use facts
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "query": query,
                "total_retrieved": retrieval_result.total_retrieved,
                "embedding_model": self.embedding_model,
                # Track routing decisions
                "routing_path": retrieval_result.routing_path,
                "retrieval_per_layer": {
                    layer: len(results)
                    for layer, results in retrieval_result.results_by_layer.items()
                },
            },
        )

    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """Get context for a specific layer using vector retrieval."""
        query = self._build_query_from_node(scope.target_node)
        project_id = self._get_project_id(scope)

        # Retrieve just this layer
        retrieval_result = self.retriever.retrieve(
            query=query,
            project_id=project_id,
            chart_id=str(scope.chart.id),
            node_id=str(scope.target_node.id),
            top_k_per_layer=self.top_k_per_layer,
            layers=[layer],
        )

        results = retrieval_result.get_layer(layer)

        if results:
            # No scores in content - just the actual content
            content = "\n\n".join(r.content for r in results)
            positional_index = results[0].positional_index if results else None
            avg_similarity = sum(r.similarity_score for r in results) / len(results)
        else:
            content = f"No embeddings found for layer {layer}"
            positional_index = None
            avg_similarity = 0.0

        return LayerContext(
            layer=layer,
            layer_name=get_layer_name(layer),
            content=content,
            metadata={
                "retrieved_count": len(results),
                "avg_similarity": avg_similarity,  # Score in metadata, not content
                "top_similarity": results[0].similarity_score if results else 0,
            },
            positional_index=positional_index,
        )

    def _ensure_embeddings(self, scope: EvaluationScope) -> None:
        """
        Ensure embeddings exist with proper parent-child links for routing.

        H-MEM uses parent-child pointers to enable efficient top-down
        retrieval where parent results constrain child search.
        """
        project_id = self._get_project_id(scope)
        chart_id = str(scope.chart.id)
        node_id = str(scope.target_node.id)

        # L1: Domain (Project level) - no parent
        l1_content = self._build_domain_content(scope)
        l1_index = HMEMLayerEmbedding.build_positional_index(
            layer=1, project_id=project_id
        )
        l1_entry = self.retriever.store_embedding(
            content=l1_content,
            layer=1,
            project_id=project_id,
            parent_index=None,  # L1 has no parent
        )

        # L2: Category (Chart level) - parent = L1
        l2_content = self._build_category_content(scope)
        l2_index = HMEMLayerEmbedding.build_positional_index(
            layer=2, project_id=project_id, chart_id=chart_id
        )
        l2_entry = self.retriever.store_embedding(
            content=l2_content,
            layer=2,
            project_id=project_id,
            chart_id=chart_id,
            chart=scope.chart,
            parent_index=l1_index,  # Link to L1
        )
        # Register L2 as child of L1
        l1_entry.add_child(l2_index)

        # L3: Trace (Path level) - parent = L2
        # Get FULL path (backward AND forward), not just immediate neighbors
        backward_path, forward_path = self._get_full_path(scope)

        if backward_path or forward_path:
            # Hash includes both directions for unique identification
            all_path_nodes = backward_path + forward_path
            path_hash = (
                compute_path_hash(all_path_nodes) if all_path_nodes else "no_path"
            )
            # Build L3 with FULL path summaries (previous AND future)
            l3_content = self._build_trace_content_with_summaries(
                scope, backward_path, forward_path
            )
            l3_index = HMEMLayerEmbedding.build_positional_index(
                layer=3,
                project_id=project_id,
                chart_id=chart_id,
                path_hash=path_hash,
            )
            l3_entry = self.retriever.store_embedding(
                content=l3_content,
                layer=3,
                project_id=project_id,
                chart_id=chart_id,
                path_hash=path_hash,
                chart=scope.chart,
                parent_index=l2_index,  # Link to L2
            )
            # Register L3 as child of L2
            l2_entry.add_child(l3_index)
            l3_parent_for_l4 = l3_index
        else:
            # No path - L4 links directly to L2
            l3_parent_for_l4 = l2_index
            l3_entry = None

        # L4: Episode (Node level) - parent = L3 (or L2 if no L3)
        l4_content = self._build_episode_content(scope)
        l4_index = HMEMLayerEmbedding.build_positional_index(
            layer=4,
            project_id=project_id,
            chart_id=chart_id,
            node_id=node_id,
        )
        self.retriever.store_embedding(
            content=l4_content,
            layer=4,
            project_id=project_id,
            chart_id=chart_id,
            node_id=node_id,
            node=scope.target_node,
            chart=scope.chart,
            parent_index=l3_parent_for_l4,  # Link to L3 (or L2)
        )
        # Register L4 as child of its parent
        if l3_entry:
            l3_entry.add_child(l4_index)
        else:
            l2_entry.add_child(l4_index)

    def _build_layer_contexts(
        self,
        scope: EvaluationScope,
        retrieval_result: HMEMContextResult,
    ) -> list[LayerContext]:
        """
        Build LayerContext objects from retrieval results.

        Faithful to H-MEM paper (Sun & Zeng 2025):
        - ALL layers (including L3) use embedding retrieval
        - L3 stores "keywords of dialogue" (path summaries in our domain)
        - Retrieval follows hierarchical routing: L2 results constrain L3 search
        - Similarity scores kept in metadata only, NOT in content
        """
        layers = []

        for layer_num in [1, 2, 3, 4]:
            results = retrieval_result.get_layer(layer_num)

            if results:
                # Content WITHOUT scores - scores are retrieval metadata
                # Use only top result for cleaner output (avoids duplicate content)
                content = results[0].content
                positional_index = results[0].positional_index
                avg_similarity = sum(r.similarity_score for r in results) / len(results)
            else:
                # Fallback to building content directly
                content = self._build_fallback_content(scope, layer_num)
                positional_index = None
                avg_similarity = 0.0

            layers.append(
                LayerContext(
                    layer=layer_num,
                    layer_name=get_layer_name(layer_num),
                    content=content,
                    metadata={
                        "retrieved_count": len(results),
                        "avg_similarity": avg_similarity,
                        "top_similarity": (
                            results[0].similarity_score if results else 0
                        ),
                    },
                    positional_index=positional_index,
                )
            )

        return layers

    def _format_context(self, layers: list[LayerContext]) -> str:
        """Format layers into H-MEM context string."""
        layer_map = {lc.layer: lc.content for lc in layers}

        return HMEM_CONTEXT_TEMPLATE.format(
            l1_content=layer_map.get(1, "No domain context"),
            l2_content=layer_map.get(2, "No category context"),
            l3_content=layer_map.get(3, "No trace context"),
            l4_content=layer_map.get(4, "No episode context"),
        )

    def _build_query_from_node(self, node: Any) -> str:
        """Build a query string from a node."""
        parts = [node.name]
        if node.description:
            parts.append(node.description[:500])

        # Add component values
        components = getattr(node, "components", None)
        if components:
            comp_list = components.all() if hasattr(components, "all") else []
            for comp in comp_list[:5]:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                value = getattr(comp, "value", "")
                if def_name and value:
                    parts.append(f"{def_name}: {value}")

        return " ".join(parts)

    def _get_project_id(self, scope: EvaluationScope) -> str:
        """Get project ID from scope or default."""
        if scope.game_concept:
            return str(getattr(scope.game_concept, "id", "default"))
        return "default"

    def _build_domain_content(self, scope: EvaluationScope) -> str:
        """
        Build L1 domain content from project context.
        """
        parts = []

        if scope.game_concept:
            content = getattr(scope.game_concept, "content", "")
            if content:
                # Include full game concept - it's project-level context
                parts.append(f"Game Concept:\n{content}")

        if scope.project_pillars:
            pillar_texts = []
            for p in scope.project_pillars:  # Include all pillars, not just first 5
                name = getattr(p, "name", "")
                desc = getattr(p, "description", "")
                # Include full pillar descriptions
                pillar_texts.append(f"- {name}: {desc}")
            parts.append("Design Pillars:\n" + "\n".join(pillar_texts))

        return "\n\n".join(parts) if parts else "No project context available"

    def _build_category_content(self, scope: EvaluationScope) -> str:
        """Build L2 category content from chart."""
        chart = scope.chart
        parts = [
            f"Chart: {chart.name}",
            f"Description: {chart.description or 'N/A'}",
        ]

        containers = getattr(chart, "containers", None)
        if containers:
            count = containers.count() if hasattr(containers, "count") else 0
            parts.append(f"Contains {count} nodes")

        return "\n".join(parts)

    def _get_full_path(self, scope: EvaluationScope) -> tuple[list[Any], list[Any]]:
        """
        Get the FULL path through the target node (backward AND forward).

        This is critical for coherence checking - we need to see:
        - What came BEFORE (to check prerequisites, story setup)
        - What comes AFTER (to check if target properly sets up future nodes)

        For a campaign I→II→III→IV→V→VI→VII→VIII, when evaluating node IV:
        - Backward: [I, II, III]
        - Forward: [V, VI, VII, VIII]

        Returns:
            Tuple of (backward_path, forward_path)
        """
        # Use get_all_paths_through_node which traces both directions
        all_paths = get_all_paths_through_node(
            scope.target_node,
            scope.chart,
            max_length=20,  # Support paths up to 20 nodes
        )

        if not all_paths:
            return [], []

        # Get the longest path and split at target
        best_backward: list[Any] = []
        best_forward: list[Any] = []
        target_node = scope.target_node

        for path in all_paths:
            try:
                target_idx = path.index(target_node)
                backward_portion = path[:target_idx]  # Everything before target
                forward_portion = path[target_idx + 1 :]  # Everything after target

                if len(backward_portion) > len(best_backward):
                    best_backward = backward_portion
                if len(forward_portion) > len(best_forward):
                    best_forward = forward_portion
            except ValueError:
                continue

        return best_backward, best_forward

    def _build_trace_content_with_summaries(
        self,
        scope: EvaluationScope,
        backward_path: list[Any],
        forward_path: list[Any],
    ) -> str:
        """
        Build L3 trace content with FULL path summaries (backward AND forward).

        For coherence checking, we need both:
        - PREVIOUS nodes: To verify prerequisites, story continuity from past
        - FUTURE nodes: To verify target properly sets up what comes next

        Args:
            scope: Evaluation scope
            backward_path: Nodes before target (start to just before target)
            forward_path: Nodes after target (just after target to end)
        """
        parts = []

        # Previous nodes (what came before)
        if backward_path:
            parts.append("PREVIOUS NODES (Path leading to target):")
            for i, node in enumerate(backward_path, 1):
                node_summary = self._summarize_node_for_trace(node)
                parts.append(f"  {i}. {node.name}: {node_summary}")

            # Add accumulated context summary
            accumulated = self._compute_accumulated_context(backward_path)
            if accumulated:
                parts.append(f"\nAccumulated Context: {accumulated}")
        else:
            parts.append("PREVIOUS NODES: None (this is the start of the path)")

        # Future nodes (what comes after) - INCLUDE FULL CONTENT
        if forward_path:
            parts.append("\nFUTURE NODES (What comes after target):")
            for i, node in enumerate(forward_path, 1):
                node_summary = self._summarize_node_for_trace(node)
                parts.append(f"  {i}. {node.name}: {node_summary}")
        else:
            parts.append("\nFUTURE NODES: None (this is the end of the path)")

        return "\n".join(parts)

    def _summarize_node_for_trace(self, node: Any) -> str:
        """
        Create a summary of a node for L3 trace.

        This creates the "keyword summary" that H-MEM expects at L3.
        We include the full description to preserve context, plus component values.
        """
        parts = []

        # Include full description - don't truncate arbitrarily
        description = getattr(node, "description", "")
        if description:
            parts.append(description)

        # Include ALL component values (they're important context)
        components = getattr(node, "components", None)
        if components:
            comp_list = components.all() if hasattr(components, "all") else []
            key_comps = []
            for comp in comp_list:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                value = getattr(comp, "value", "")
                if def_name and value is not None:
                    key_comps.append(f"{def_name}={value}")
            if key_comps:
                parts.append(f"[{', '.join(key_comps)}]")

        return " ".join(parts) if parts else "(no details)"

    def _compute_accumulated_context(self, path_nodes: list[Any]) -> str:
        """
        Compute accumulated context summary from path.

        This captures what the player "has" or "knows" at this point
        based on traversing the path.
        """
        mechanics_introduced = []
        narrative_events = []

        for node in path_nodes:
            desc = getattr(node, "description", "") or ""
            desc_lower = desc.lower()

            # Look for mechanics introduction keywords
            if any(kw in desc_lower for kw in ["introduces", "teaches", "learn"]):
                mechanics_introduced.append(node.name)

            # Look for narrative event keywords
            if any(
                kw in desc_lower
                for kw in ["discovers", "reveals", "meets", "defeats", "escapes"]
            ):
                narrative_events.append(node.name)

        parts = []
        if mechanics_introduced:
            parts.append(f"Mechanics from: {', '.join(mechanics_introduced)}")
        if narrative_events:
            parts.append(f"Story events in: {', '.join(narrative_events)}")

        return "; ".join(parts) if parts else ""

    def _build_episode_content(self, scope: EvaluationScope) -> str:
        """Build L4 episode content from target node."""
        node = scope.target_node
        parts = [
            f"Node: {node.name}",
            f"Description: {node.description or 'N/A'}",
        ]

        components = getattr(node, "components", None)
        if components:
            comp_list = components.all() if hasattr(components, "all") else []
            for comp in comp_list:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                value = getattr(comp, "value", "")
                parts.append(f"- {def_name}: {value}")

        return "\n".join(parts)

    def _build_fallback_content(self, scope: EvaluationScope, layer: int) -> str:
        """Build fallback content when no embeddings found."""
        if layer == 1:
            return self._build_domain_content(scope)
        elif layer == 2:
            return self._build_category_content(scope)
        elif layer == 3:
            # Use FULL path (backward AND forward) for fallback too
            backward_path, forward_path = self._get_full_path(scope)
            return self._build_trace_content_with_summaries(
                scope, backward_path, forward_path
            )
        else:
            return self._build_episode_content(scope)

    @property
    def requires_embeddings(self) -> bool:
        """H-MEM requires vector embeddings."""
        return True

    @property
    def requires_llm(self) -> bool:
        """LLM is optional (for summarization only)."""
        return False
