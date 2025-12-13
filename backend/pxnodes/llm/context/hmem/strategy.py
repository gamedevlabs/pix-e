"""
H-MEM Strategy Implementation.

Implements the true H-MEM approach from Sun & Zeng (2025) using
vector embeddings with positional index routing.

Key differences from Hierarchical Graph:
- Uses vector similarity instead of graph traversal
- Stores embeddings for each layer in Django model
- Positional index encoding for hierarchical routing
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
from pxnodes.llm.context.hmem.retriever import (
    HMEMContextResult,
    HMEMRetriever,
    compute_path_hash,
)
from pxnodes.llm.context.shared.graph_retrieval import get_graph_slice

# H-MEM context template
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
    H-MEM strategy using vector embeddings and positional index routing.

    This is the faithful implementation of Sun & Zeng (2025) "H-MEM:
    Hierarchical Memory for High-Efficiency Long-Term Reasoning".

    Unlike HierarchicalGraphStrategy which uses deterministic graph
    traversal, this strategy uses:
    - Vector embeddings for semantic similarity matching
    - Positional index encoding for hierarchical routing
    - Django model storage for persistent embeddings

    Use this when:
    - Semantic similarity is important for finding relevant context
    - You want to leverage pre-computed embeddings
    - The graph structure alone doesn't capture semantic relationships
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
        3. Retrieve relevant context per layer using vector similarity
        4. Format into hierarchical context string

        Args:
            scope: Evaluation scope with target node and chart
            query: Optional custom query (defaults to node description)

        Returns:
            ContextResult with H-MEM hierarchical context
        """
        # Build query from node if not provided
        if not query:
            query = self._build_query_from_node(scope.target_node)

        # Auto-embed if needed
        if self.auto_embed:
            self._ensure_embeddings(scope)

        # Get project ID
        project_id = self._get_project_id(scope)

        # Retrieve from H-MEM
        retrieval_result = self.retriever.retrieve(
            query=query,
            project_id=project_id,
            chart_id=str(scope.chart.id),
            node_id=str(scope.target_node.id),
            top_k_per_layer=self.top_k_per_layer,
        )

        # Build layer contexts
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
            content = "\n\n".join(r.content for r in results)
            positional_index = results[0].positional_index if results else None
        else:
            content = f"No embeddings found for layer {layer}"
            positional_index = None

        return LayerContext(
            layer=layer,
            layer_name=get_layer_name(layer),
            content=content,
            metadata={
                "retrieved_count": len(results),
                "top_similarity": results[0].similarity_score if results else 0,
            },
            positional_index=positional_index,
        )

    def _ensure_embeddings(self, scope: EvaluationScope) -> None:
        """Ensure embeddings exist for the evaluation scope."""
        project_id = self._get_project_id(scope)
        chart_id = str(scope.chart.id)
        node_id = str(scope.target_node.id)

        # L1: Domain (Project level)
        l1_content = self._build_domain_content(scope)
        if l1_content:
            self.retriever.store_embedding(
                content=l1_content,
                layer=1,
                project_id=project_id,
            )

        # L2: Category (Chart level)
        l2_content = self._build_category_content(scope)
        self.retriever.store_embedding(
            content=l2_content,
            layer=2,
            project_id=project_id,
            chart_id=chart_id,
            chart=scope.chart,
        )

        # L3: Trace (Path level) - embed path context
        graph_slice = get_graph_slice(scope.target_node, scope.chart, depth=scope.depth)
        if graph_slice.previous_nodes:
            path_hash = compute_path_hash(graph_slice.previous_nodes)
            l3_content = self._build_trace_content(scope, graph_slice)
            self.retriever.store_embedding(
                content=l3_content,
                layer=3,
                project_id=project_id,
                chart_id=chart_id,
                path_hash=path_hash,
                chart=scope.chart,
            )

        # L4: Episode (Node level)
        l4_content = self._build_episode_content(scope)
        self.retriever.store_embedding(
            content=l4_content,
            layer=4,
            project_id=project_id,
            chart_id=chart_id,
            node_id=node_id,
            node=scope.target_node,
            chart=scope.chart,
        )

    def _build_layer_contexts(
        self,
        scope: EvaluationScope,
        retrieval_result: HMEMContextResult,
    ) -> list[LayerContext]:
        """Build LayerContext objects from retrieval results."""
        layers = []

        for layer_num in [1, 2, 3, 4]:
            results = retrieval_result.get_layer(layer_num)

            if results:
                # Combine top results for this layer
                content = "\n\n".join(
                    f"[Score: {r.similarity_score:.3f}]\n{r.content}"
                    for r in results[: self.top_k_per_layer]
                )
                positional_index = results[0].positional_index
            else:
                # Fallback to building content directly
                content = self._build_fallback_content(scope, layer_num)
                positional_index = None

            layers.append(
                LayerContext(
                    layer=layer_num,
                    layer_name=get_layer_name(layer_num),
                    content=content,
                    metadata={
                        "retrieved_count": len(results),
                        "top_similarity": results[0].similarity_score if results else 0,
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
        """Build L1 domain content from project context."""
        parts = []

        if scope.game_concept:
            content = getattr(scope.game_concept, "content", "")
            if content:
                parts.append(f"Game Concept: {content[:1000]}")

        if scope.project_pillars:
            pillar_texts = []
            for p in scope.project_pillars[:5]:
                name = getattr(p, "name", "")
                desc = getattr(p, "description", "")[:200]
                pillar_texts.append(f"{name}: {desc}")
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

    def _build_trace_content(self, scope: EvaluationScope, graph_slice: Any) -> str:
        """Build L3 trace content from path."""
        parts = []

        if graph_slice.previous_nodes:
            path_names = [n.name for n in graph_slice.previous_nodes]
            parts.append(f"Path: {' -> '.join(path_names)}")

        if graph_slice.next_nodes:
            next_names = [n.name for n in graph_slice.next_nodes]
            parts.append(f"Leads to: {', '.join(next_names)}")

        return "\n".join(parts) if parts else "Start of path"

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
            graph_slice = get_graph_slice(
                scope.target_node, scope.chart, depth=scope.depth
            )
            return self._build_trace_content(scope, graph_slice)
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
