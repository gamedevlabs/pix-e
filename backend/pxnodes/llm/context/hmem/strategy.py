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

import hashlib
import logging
import re
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
        self._trace_summary_state_map: dict[str, Any] = {}
        self._trace_summary_chart: Optional[Any] = None

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
                "includes_target_description": True,
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

        # L1: Domain (Project level) - multiple entries per aspect/pillar
        l1_items = []
        l1_indices = []
        for key, content in self._build_domain_entries(scope):
            l1_index = HMEMLayerEmbedding.build_positional_index(
                layer=1, project_id=project_id, path_hash=key
            )
            l1_items.append(
                {
                    "content": content,
                    "layer": 1,
                    "project_id": project_id,
                    "chart_id": "",
                    "path_hash": key,
                    "node_id": "",
                    "node": None,
                    "chart": None,
                    "parent_index": None,
                    "positional_index": l1_index,
                }
            )
            l1_indices.append(l1_index)
        l1_entries = self._store_embeddings_batch(l1_items)

        # L2: Category (Chart level) - split entries
        l2_items = []
        l2_indices = []
        for key, content in self._build_category_entries(scope):
            l2_index = HMEMLayerEmbedding.build_positional_index(
                layer=2, project_id=project_id, chart_id=chart_id, path_hash=key
            )
            l2_items.append(
                {
                    "content": content,
                    "layer": 2,
                    "project_id": project_id,
                    "chart_id": chart_id,
                    "path_hash": key,
                    "node_id": "",
                    "node": None,
                    "chart": scope.chart,
                    "parent_index": l1_indices[0] if l1_indices else None,
                    "positional_index": l2_index,
                }
            )
            l2_indices.append(l2_index)
        l2_entries = self._store_embeddings_batch(l2_items)

        # Register all L2 as children of all L1 entries
        for l1_entry in l1_entries:
            for l2_index in l2_indices:
                l1_entry.add_child(l2_index)

        # L3: Trace (Path level) - snippets + node summaries + milestones
        backward_path, forward_path = self._get_full_path(scope)
        from pxnodes.llm.context.change_detection import get_processing_state_map

        path_nodes = backward_path + forward_path
        self._trace_summary_state_map = get_processing_state_map(
            scope.chart, path_nodes
        )
        self._trace_summary_chart = scope.chart
        l3_items = []
        l3_indices = []
        for key, content in self._build_trace_entries(
            scope, backward_path, forward_path
        ):
            l3_index = HMEMLayerEmbedding.build_positional_index(
                layer=3,
                project_id=project_id,
                chart_id=chart_id,
                path_hash=key,
            )
            l3_items.append(
                {
                    "content": content,
                    "layer": 3,
                    "project_id": project_id,
                    "chart_id": chart_id,
                    "path_hash": key,
                    "node_id": "",
                    "node": None,
                    "chart": scope.chart,
                    "parent_index": l2_indices[0] if l2_indices else None,
                    "positional_index": l3_index,
                }
            )
            l3_indices.append(l3_index)
        l3_entries = self._store_embeddings_batch(l3_items)

        # Register all L3 as children of all L2 entries
        for l2_entry in l2_entries:
            for l3_index in l3_indices:
                l2_entry.add_child(l3_index)

        l3_parent_for_l4 = (
            l3_indices[0] if l3_indices else (l2_indices[0] if l2_indices else None)
        )

        # L4: Episode (Node level) - parent = L3 (or L2 if no L3)
        l4_content = self._build_episode_content(scope)
        l4_index = HMEMLayerEmbedding.build_positional_index(
            layer=4,
            project_id=project_id,
            chart_id=chart_id,
            node_id=node_id,
        )
        # Store L4 embeddings (result not used, but method has side effects)
        self._store_embeddings_batch(
            [
                {
                    "content": l4_content,
                    "layer": 4,
                    "project_id": project_id,
                    "chart_id": chart_id,
                    "path_hash": "",
                    "node_id": node_id,
                    "node": scope.target_node,
                    "chart": scope.chart,
                    "parent_index": l3_parent_for_l4,  # Link to L3 (or L2)
                    "positional_index": l4_index,
                }
            ]
        )
        # Register L4 as child of all L3 entries (or L2 entries if no L3)
        if l3_entries:
            for l3_entry in l3_entries:
                l3_entry.add_child(l4_index)
        else:
            for l2_entry in l2_entries:
                l2_entry.add_child(l4_index)

    def _build_domain_entries(self, scope: EvaluationScope) -> list[tuple[str, str]]:
        """Build L1 entries for each game concept aspect and pillar."""
        entries: list[tuple[str, str]] = []

        content = ""
        if scope.game_concept:
            content = getattr(scope.game_concept, "content", "") or ""

        if content:
            overview, sections = self._split_game_concept_sections(content)
            if overview:
                entries.append(
                    ("concept_overview", f"Game Concept Overview:\n{overview}")
                )
            for name, text in sections:
                key = f"concept_{self._slugify(name)}"
                entries.append((key, f"{name}:\n{text}"))
        else:
            entries.append(("concept_overview", "Game Concept Overview: N/A"))

        if scope.project_pillars:
            for pillar in scope.project_pillars:
                name = getattr(pillar, "name", "") or "pillar"
                desc = getattr(pillar, "description", "") or ""
                key = f"pillar_{self._slugify(name)}"
                entries.append((key, f"Pillar: {name}\nDescription: {desc}"))

        if not entries:
            entries.append(("project_context", "No project context available."))

        return entries

    def _build_category_entries(self, scope: EvaluationScope) -> list[tuple[str, str]]:
        """Build L2 entries for chart-level splits."""
        chart = scope.chart
        nodes = self._get_chart_nodes(chart)
        node_names = [getattr(node, "name", "") for node in nodes if node]

        entries: list[tuple[str, str]] = []

        overview = [
            f"Chart: {chart.name}",
            f"Description: {chart.description or 'N/A'}",
            f"Total Nodes: {len(nodes)}",
        ]
        entries.append(("chart_overview", "\n".join(overview)))

        if node_names:
            nodes_text = ", ".join(node_names[:30])
            entries.append(("chart_nodes", f"Nodes: {nodes_text}"))

        pacing_lines = []
        pacing_values: list[float] = []
        for node in nodes:
            node_name = getattr(node, "name", "") or "Unnamed"
            planned = self._get_node_component_value(node, "Planned Time to Complete")
            if planned is not None:
                pacing_lines.append(f"{node_name}: {planned}")
                try:
                    pacing_values.append(float(planned))
                except (TypeError, ValueError):
                    pass
        if pacing_lines:
            summary = ""
            if pacing_values:
                avg = sum(pacing_values) / len(pacing_values)
                summary = f"\nAverage Planned Time: {avg:.1f}"
            entries.append(
                (
                    "chart_pacing",
                    "Planned Time by Node:\n" + "\n".join(pacing_lines) + summary,
                )
            )

        mechanics = self._get_chart_component_names(nodes)
        if mechanics:
            entries.append(
                (
                    "chart_mechanics",
                    "Chart Mechanics Focus:\n" + ", ".join(sorted(mechanics)),
                )
            )

        narrative_summary = self._summarize_chart_narrative(nodes)
        if narrative_summary:
            entries.append(("chart_narrative", narrative_summary))

        return entries

    def _build_trace_entries(
        self,
        scope: EvaluationScope,
        backward_path: list[Any],
        forward_path: list[Any],
    ) -> list[tuple[str, str]]:
        """Build L3 entries from path snippets, node summaries, and milestones."""
        entries: list[tuple[str, str]] = []
        full_path = list(backward_path) + [scope.target_node] + list(forward_path)
        if not full_path:
            return entries

        path_id = compute_path_hash(full_path)
        summaries = self._summarize_nodes_for_trace(full_path)

        for idx, (node, summary) in enumerate(zip(full_path, summaries)):
            node_name = getattr(node, "name", "") or f"node_{idx + 1}"
            key = f"{path_id}_node_{idx + 1}_{self._slugify(node_name)}"
            entries.append((key, f"Node: {node_name}\nSummary: {summary}"))

        for window_size in (2, 3):
            if len(full_path) < window_size:
                continue
            for i in range(len(full_path) - window_size + 1):
                snippet_nodes = full_path[i : i + window_size]
                snippet_names = " -> ".join(
                    getattr(node, "name", "") or f"Node {i + 1}"
                    for node in snippet_nodes
                )
                snippet_summaries = "; ".join(summaries[i : i + window_size])
                key = f"{path_id}_path_{window_size}_{i + 1}"
                snippet_text = (
                    f"Path snippet: {snippet_names}\nHighlights: {snippet_summaries}"
                )
                entries.append(
                    (
                        key,
                        snippet_text,
                    )
                )

        milestones = self._extract_path_milestones(full_path, summaries)
        for idx, milestone in enumerate(milestones, 1):
            key = f"{path_id}_milestone_{idx}"
            entries.append((key, f"Milestone: {milestone}"))

        return entries

    def _split_game_concept_sections(
        self, content: str
    ) -> tuple[str, list[tuple[str, str]]]:
        """Split game concept into overview and named sections."""
        lines = [line.rstrip() for line in content.splitlines()]
        overview_lines: list[str] = []
        sections: list[tuple[str, list[str]]] = []
        current_name: Optional[str] = None
        current_lines: list[str] = []
        heading_re = re.compile(r"^\*\*(.+?)\*\*$")

        for line in lines:
            heading = heading_re.match(line.strip())
            if heading:
                if current_name:
                    sections.append((current_name, current_lines))
                current_name = heading.group(1).strip()
                current_lines = []
                continue
            if current_name:
                current_lines.append(line)
            else:
                overview_lines.append(line)

        if current_name:
            sections.append((current_name, current_lines))

        overview = "\n".join(line for line in overview_lines if line.strip()).strip()
        section_entries = [
            (name, "\n".join(line for line in lines if line.strip()).strip())
            for name, lines in sections
            if any(line.strip() for line in lines)
        ]
        return overview, section_entries

    def _extract_path_milestones(
        self, path_nodes: list[Any], summaries: list[str]
    ) -> list[str]:
        """Extract milestone summaries from a path."""
        if not path_nodes:
            return []

        if self.llm_provider:
            node_lines = []
            for node, summary in zip(path_nodes, summaries):
                node_lines.append(f"- {getattr(node, 'name', '')}: {summary}")
            prompt = (
                "Extract 3-6 key milestones from the path. "
                "Return each milestone as a short phrase on its own line.\n\n"
                + "\n".join(node_lines)
            )
            try:
                response = self.llm_provider.generate(prompt)
                milestones_list = [
                    line.strip("- ").strip()
                    for line in response.splitlines()
                    if line.strip()
                ]
                return [m for m in milestones_list if m]
            except Exception:
                logger.warning("Milestone extraction LLM failed, falling back.")

        milestones: list[str] = []
        for node in path_nodes:
            description = getattr(node, "description", "") or ""
            lower = description.lower()
            if any(
                term in lower
                for term in [
                    "introduces",
                    "introduce",
                    "unlocks",
                    "culminates",
                    "finale",
                ]
            ):
                sentence = description.split(".")[0].strip()
                if sentence:
                    milestones.append(sentence)

        if path_nodes:
            first_name = getattr(path_nodes[0], "name", "") or "Start"
            last_name = getattr(path_nodes[-1], "name", "") or "End"
            milestones.insert(0, f"Start of path: {first_name}")
            if last_name != first_name:
                milestones.append(f"End of path: {last_name}")

        deduped: list[str] = []
        seen = set()
        for item in milestones:
            if item and item not in seen:
                deduped.append(item)
                seen.add(item)
        return deduped[:6]

    def _slugify(self, value: str) -> str:
        """Normalize a string for positional index keys."""
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
        normalized = normalized.strip("_")
        return normalized or "entry"

    def _get_chart_nodes(self, chart: Any) -> list[Any]:
        """Return chart nodes from containers if available."""
        containers = getattr(chart, "containers", None)
        if not containers:
            return []
        if hasattr(containers, "filter"):
            containers = containers.filter(content__isnull=False)
        container_list = (
            containers.all() if hasattr(containers, "all") else list(containers)
        )
        nodes = [c.content for c in container_list if getattr(c, "content", None)]
        return nodes

    def _get_node_component_value(
        self, node: Any, component_name: str
    ) -> Optional[Any]:
        """Return a component value by definition name."""
        components = getattr(node, "components", None)
        if not components:
            return None
        comp_list = components.all() if hasattr(components, "all") else []
        for comp in comp_list:
            def_name = getattr(getattr(comp, "definition", None), "name", "")
            if def_name == component_name:
                return getattr(comp, "value", None)
        return None

    def _get_chart_component_names(self, nodes: list[Any]) -> set[str]:
        """Collect component definition names from chart nodes."""
        names: set[str] = set()
        for node in nodes:
            components = getattr(node, "components", None)
            comp_list = (
                components.all() if components and hasattr(components, "all") else []
            )
            for comp in comp_list:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                if def_name and def_name != "Planned Time to Complete":
                    names.add(def_name)
        return names

    def _summarize_chart_narrative(self, nodes: list[Any]) -> str:
        """Summarize chart narrative arc."""
        if not nodes:
            return ""
        if self.llm_provider:
            node_lines = []
            for node in nodes:
                name = getattr(node, "name", "")
                desc = getattr(node, "description", "") or ""
                node_lines.append(f"- {name}: {desc}")
            prompt = (
                "Summarize the chart narrative arc in 2-3 sentences.\n\n"
                + "\n".join(node_lines)
            )
            try:
                response = self.llm_provider.generate(prompt)
                summary = response.strip()
                if summary:
                    return "Chart Narrative Arc:\n" + summary
            except Exception:
                logger.warning("Chart narrative LLM failed, falling back.")

        sentences = []
        for node in nodes[:5]:
            desc = getattr(node, "description", "") or ""
            if desc:
                sentences.append(desc.split(".")[0].strip())
        if sentences:
            return "Chart Narrative Arc:\n" + " ".join(sentences)
        return ""

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
                content = "\n\n".join(r.content for r in results)
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

    def _store_embeddings_batch(
        self, items: list[dict[str, Any]]
    ) -> list[HMEMLayerEmbedding]:
        """Store embeddings in batches to reduce sequential API calls."""
        if not items:
            return []

        generator = self.retriever.embedding_generator
        embedding_model = self.retriever.embedding_model
        embedding_dim = self.retriever.embedding_dim

        instances: list[HMEMLayerEmbedding] = []
        to_embed: list[dict[str, Any]] = []

        for item in items:
            content = item["content"]
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:64]
            positional_index = item["positional_index"]
            existing = HMEMLayerEmbedding.objects.filter(
                positional_index=positional_index,
                content_hash=content_hash,
            ).first()
            if existing:
                parent_index = item.get("parent_index")
                if parent_index and existing.parent_index != parent_index:
                    existing.parent_index = parent_index
                    existing.save(update_fields=["parent_index"])
                instances.append(existing)
            else:
                item["content_hash"] = content_hash
                to_embed.append(item)

        if to_embed:
            embeddings = generator.generate_embeddings_batch(
                [item["content"] for item in to_embed]
            )
            for item, embedding in zip(to_embed, embeddings):
                instance, _ = HMEMLayerEmbedding.objects.update_or_create(
                    positional_index=item["positional_index"],
                    defaults={
                        "layer": item["layer"],
                        "content": item["content"],
                        "embedding": embedding,
                        "embedding_model": embedding_model,
                        "embedding_dim": embedding_dim,
                        "content_hash": item["content_hash"],
                        "node": item.get("node"),
                        "chart": item.get("chart"),
                        "parent_index": item.get("parent_index"),
                        "child_indices": [],
                    },
                )
                instances.append(instance)

        return instances

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
        accumulated = ""
        backward_summaries: list[str] = []
        forward_summaries: list[str] = []

        path_nodes = backward_path + forward_path
        if path_nodes:
            if self.llm_provider:
                try:
                    import asyncio

                    import logfire

                    async def run_parallel() -> tuple[list[str], str]:
                        with logfire.span(
                            "hmem.trace_parallel_extraction",
                            total_nodes=len(path_nodes),
                            backward_count=len(backward_path),
                            forward_count=len(forward_path),
                            include_accumulated=bool(backward_path),
                        ):
                            summary_tasks = [
                                asyncio.to_thread(self._summarize_node_for_trace, node)
                                for node in path_nodes
                            ]
                            tasks = list(summary_tasks)
                            if backward_path:
                                tasks.append(
                                    asyncio.to_thread(
                                        self._compute_accumulated_context, backward_path
                                    )
                                )
                            results = await asyncio.gather(
                                *tasks, return_exceptions=True
                            )

                        summaries: list[str] = []
                        for result in results[: len(path_nodes)]:
                            if isinstance(result, Exception):
                                summaries.append("(no details)")
                            else:
                                summaries.append(str(result))

                        acc = ""
                        if backward_path:
                            acc_result = results[len(path_nodes)]
                            acc = (
                                ""
                                if isinstance(acc_result, Exception)
                                else str(acc_result)
                            )

                        return summaries, acc

                    summaries, accumulated = asyncio.run(run_parallel())
                    backward_summaries = summaries[: len(backward_path)]
                    forward_summaries = summaries[len(backward_path) :]
                except RuntimeError:
                    for node in backward_path:
                        backward_summaries.append(self._summarize_node_for_trace(node))
                    for node in forward_path:
                        forward_summaries.append(self._summarize_node_for_trace(node))
                    if backward_path:
                        accumulated = self._compute_accumulated_context(backward_path)
            else:
                for node in backward_path:
                    backward_summaries.append(self._summarize_node_for_trace(node))
                for node in forward_path:
                    forward_summaries.append(self._summarize_node_for_trace(node))
                if backward_path:
                    accumulated = self._compute_accumulated_context(backward_path)

        # Previous nodes (what came before)
        if backward_path:
            parts.append("PREVIOUS NODES (Path leading to target):")
            for i, node in enumerate(backward_path, 1):
                node_summary = (
                    backward_summaries[i - 1]
                    if i - 1 < len(backward_summaries)
                    else self._summarize_node_for_trace(node)
                )
                parts.append(f"  {i}. {node.name}: {node_summary}")

            if accumulated:
                parts.append(f"\nAccumulated Context: {accumulated}")
        else:
            parts.append("PREVIOUS NODES: None (this is the start of the path)")

        # Future nodes (what comes after) - INCLUDE FULL CONTENT
        if forward_path:
            parts.append("\nFUTURE NODES (What comes after target):")
            for i, node in enumerate(forward_path, 1):
                node_summary = (
                    forward_summaries[i - 1]
                    if i - 1 < len(forward_summaries)
                    else self._summarize_node_for_trace(node)
                )
                parts.append(f"  {i}. {node.name}: {node_summary}")
        else:
            parts.append("\nFUTURE NODES: None (this is the end of the path)")

        return "\n".join(parts)

    def _summarize_node_for_trace(self, node: Any) -> str:
        """
        Create a summary of a node for L3 trace.

        This creates the "keyword summary" that H-MEM expects at L3.
        """
        from pxnodes.llm.context.change_detection import (
            has_node_changed,
            update_summary_cache,
        )

        node_id = str(getattr(node, "id", ""))
        if self._trace_summary_chart and node_id:
            state = self._trace_summary_state_map.get(node_id)
            if (
                state
                and not has_node_changed(node, self._trace_summary_chart)
                and state.trace_summary
            ):
                return state.trace_summary

        description = getattr(node, "description", "") or ""
        components = getattr(node, "components", None)
        comp_list = (
            components.all() if components and hasattr(components, "all") else []
        )

        comp_lines = []
        for comp in comp_list:
            def_name = getattr(getattr(comp, "definition", None), "name", "")
            value = getattr(comp, "value", "")
            if def_name and value is not None:
                comp_lines.append(f"- {def_name}: {value}")
        comp_block = "\n".join(comp_lines) if comp_lines else "None"

        if self.llm_provider and description:
            prompt = (
                "Summarize the node in 1-2 short phrases (keywords/phrases only). "
                "Focus on mechanics and narrative events. Avoid full sentences.\n\n"
                f"Title: {getattr(node, 'name', '')}\n"
                f"Description: {description}\n"
                f"Components:\n{comp_block}\n\n"
                "Return a single line."
            )
            try:
                response = self.llm_provider.generate(prompt)
                summary = response.strip()
                if summary:
                    if self._trace_summary_chart and node_id:
                        update_summary_cache(
                            node=node,
                            chart=self._trace_summary_chart,
                            trace_summary=summary,
                        )
                    return summary
            except Exception:
                logger.warning("Trace summary LLM failed, falling back to heuristic.")

        parts = []
        if description:
            parts.append(description.split(".")[0][:180])
        if comp_lines:
            parts.append(f"[{', '.join(comp_lines)[:180]}]")
        fallback = " ".join(p for p in parts if p).strip() or "(no details)"
        if self._trace_summary_chart and node_id:
            update_summary_cache(
                node=node,
                chart=self._trace_summary_chart,
                trace_summary=fallback,
            )
        return fallback

    def _summarize_nodes_for_trace(self, nodes: list[Any]) -> list[str]:
        """Summarize multiple nodes, parallelizing LLM calls when possible."""
        if not nodes:
            return []

        if not self.llm_provider or len(nodes) == 1:
            return [self._summarize_node_for_trace(node) for node in nodes]

        try:
            import asyncio

            import logfire

            async def run_parallel() -> list[str]:
                with logfire.span(
                    "hmem.trace_summaries.generate",
                    node_count=len(nodes),
                ):
                    tasks = [
                        asyncio.to_thread(self._summarize_node_for_trace, node)
                        for node in nodes
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                summaries: list[str] = []
                for result in results:
                    if isinstance(result, Exception):
                        summaries.append("(no details)")
                    else:
                        summaries.append(str(result))
                return summaries

            return asyncio.run(run_parallel())
        except RuntimeError:
            return [self._summarize_node_for_trace(node) for node in nodes]

    def _compute_accumulated_context(self, path_nodes: list[Any]) -> str:
        """
        Compute accumulated context summary from path.

        This captures what the player "has" or "knows" at this point
        based on traversing the path.
        """
        if not path_nodes:
            return ""

        if self.llm_provider:
            node_summaries = []
            for node in path_nodes:
                node_summaries.append(
                    f"- {getattr(node, 'name', '')}: {getattr(node, 'description', '')}"
                )

            prompt = (
                "From the previous nodes, extract accumulated player context.\n"
                "Return exactly two lines:\n"
                "Mechanics Introduced: <short list>\n"
                "Story Events: <short list>\n\n"
                "Nodes:\n" + "\n".join(node_summaries)
            )
            try:
                response = self.llm_provider.generate(prompt)
                return response.strip()
            except Exception:
                logger.warning("Accumulated context LLM failed, falling back.")

        component_names = set()
        for node in path_nodes:
            components = getattr(node, "components", None)
            comp_list = (
                components.all() if components and hasattr(components, "all") else []
            )
            for comp in comp_list:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                if def_name:
                    component_names.add(def_name)

        if component_names:
            return f"Mechanics from components: {', '.join(sorted(component_names))}"
        return ""

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
