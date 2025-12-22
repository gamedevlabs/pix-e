"""
Combined Strategy Implementation.

Combines Mixed Structural Memory (Zeng et al. 2024) encoding with
H-MEM hierarchical routing (Sun & Zeng 2025).

Mixed memory structures (from Structural Memory):
- Chunks: Raw text segments
- Knowledge Triples: Structured relationships
- Atomic Facts: Indivisible information units
- Summaries: Condensed overviews

Hierarchical routing (from H-MEM):
- L1 Domain: Project-level context (concept aspects + pillars)
- L2 Category: Chart-level context splits
- L3 Trace: Path snippets + node summaries + milestones
- L4 Episode: Target node with mixed memory encoding
"""

from typing import Any, Optional, Union

import logfire

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import LLMProvider
from pxnodes.llm.context.base.types import ContextResult, EvaluationScope, StrategyType
from pxnodes.llm.context.hmem.retriever import HMEMContextResult, compute_path_hash
from pxnodes.llm.context.hmem.strategy import HMEMStrategy
from pxnodes.llm.context.structural_memory.chunks import extract_chunks
from pxnodes.llm.context.structural_memory.facts import extract_atomic_facts
from pxnodes.llm.context.structural_memory.summaries import (
    create_fallback_summary,
    extract_summary,
)
from pxnodes.llm.context.structural_memory.triples import extract_llm_triples_only

COMBINED_CONTEXT_TEMPLATE = """### COMBINED CONTEXT (SM Mixed + HMEM Routing)

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


@StrategyRegistry.register(StrategyType.COMBINED)
class CombinedStrategy(HMEMStrategy):
    """
    Combined strategy: Mixed Structural Memory encoding + HMEM routing.

    Uses H-MEM hierarchical retrieval for L1-L3, while L4 embeds the
    target node using mixed memory (chunks + triples + atomic facts + summary).
    """

    strategy_type = StrategyType.COMBINED

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        embedding_model: str = "text-embedding-3-small",
        top_k_per_layer: int = 3,
        auto_embed: bool = True,
        l2_similarity_threshold: float = 0.25,
        l3_similarity_threshold: float = 0.25,
        **kwargs: Any,
    ):
        super().__init__(
            llm_provider=llm_provider,
            embedding_model=embedding_model,
            top_k_per_layer=top_k_per_layer,
            auto_embed=auto_embed,
            **kwargs,
        )
        self._mixed_cache: dict[str, dict[str, Any]] = {}
        self.l2_similarity_threshold = l2_similarity_threshold
        self.l3_similarity_threshold = l3_similarity_threshold

    def _build_node_mixed_memory(self, node: Any) -> dict[str, Any]:
        """Build mixed memory structures for a node (sync)."""
        summary = None
        if self.llm_provider:
            summary = extract_summary(node, llm_provider=self.llm_provider)
        if not summary:
            summary = create_fallback_summary(node)

        triples = []
        facts = []
        if self.llm_provider:
            triples = extract_llm_triples_only(node, llm_provider=self.llm_provider)
            facts = extract_atomic_facts(node, llm_provider=self.llm_provider)
        chunks = extract_chunks(node)

        return {
            "summary": summary.content if summary else "",
            "triples": triples,
            "facts": facts,
            "chunks": chunks,
        }

    async def _build_node_mixed_memory_async(self, node: Any) -> dict[str, Any]:
        """Build mixed memory structures for a node (async)."""
        import asyncio
        from typing import Any as AnyType

        from pxnodes.llm.context.structural_memory.summaries import Summary

        node_name = getattr(node, "name", "")
        with logfire.span(
            "combined.mixed_memory.node.extract.async",
            node_name=node_name,
        ):
            summary_task = (
                asyncio.to_thread(extract_summary, node, self.llm_provider)
                if self.llm_provider
                else None
            )
            triple_task = (
                asyncio.to_thread(extract_llm_triples_only, node, self.llm_provider)
                if self.llm_provider
                else None
            )
            fact_task = (
                asyncio.to_thread(extract_atomic_facts, node, self.llm_provider)
                if self.llm_provider
                else None
            )
            chunks_task = asyncio.to_thread(extract_chunks, node)

            tasks: list[AnyType] = [chunks_task]
            if summary_task:
                tasks.append(summary_task)
            if triple_task:
                tasks.append(triple_task)
            if fact_task:
                tasks.append(fact_task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            chunks = results[0] if results else []
            summary: Optional[Summary] = None
            triples: list[Any] = []
            facts: list[Any] = []

            for result in results[1:]:
                if isinstance(result, (Exception, BaseException)):
                    continue
                if result is None:
                    continue
                if isinstance(result, list):
                    if result and hasattr(result[0], "fact"):
                        facts = result
                    else:
                        triples = result
                elif hasattr(result, "content"):
                    # Type narrowing: we know result has 'content' attribute
                    summary = result  # type: ignore[assignment]

            if not summary:
                summary = create_fallback_summary(node)

            return {
                "summary": summary.content if summary else "",
                "triples": triples,
                "facts": facts,
                "chunks": chunks,
            }

    def _get_node_mixed_memory(self, node: Any) -> dict[str, Any]:
        """Return mixed memory structures for a node with simple caching."""
        node_id = str(getattr(node, "id", "") or getattr(node, "name", ""))
        cached = self._mixed_cache.get(node_id)
        if cached:
            return cached

        mixed = self._build_node_mixed_memory(node)
        self._mixed_cache[node_id] = mixed
        return mixed

    def _prime_mixed_cache(self, nodes: list[Any]) -> None:
        """Precompute mixed memory for nodes in parallel when possible."""
        if not nodes:
            return

        if not self.llm_provider:
            for node in nodes:
                node_id = str(getattr(node, "id", "") or getattr(node, "name", ""))
                if node_id not in self._mixed_cache:
                    self._mixed_cache[node_id] = self._build_node_mixed_memory(node)
            return

        import asyncio

        async def run_parallel() -> list[Union[dict[str, Any], BaseException]]:
            with logfire.span(
                "combined.mixed_memory.cache_warmup",
                node_count=len(nodes),
            ):
                tasks = [self._build_node_mixed_memory_async(node) for node in nodes]
                return await asyncio.gather(
                    *tasks, return_exceptions=True
                )  # type: ignore[return-value]

        try:
            results = asyncio.run(run_parallel())
            for node, result in zip(nodes, results):
                mixed: dict[str, Any]
                if isinstance(result, (Exception, BaseException)):
                    mixed = self._build_node_mixed_memory(node)
                else:
                    mixed = result
                node_id = str(getattr(node, "id", "") or getattr(node, "name", ""))
                self._mixed_cache[node_id] = mixed
        except RuntimeError:
            for node in nodes:
                node_id = str(getattr(node, "id", "") or getattr(node, "name", ""))
                if node_id not in self._mixed_cache:
                    self._mixed_cache[node_id] = self._build_node_mixed_memory(node)

    def _format_mixed_memory_block(
        self,
        title: str,
        summary: str,
        triples: list[Any],
        facts: list[Any],
        chunks: Optional[list[Any]] = None,
        max_triples: int = 8,
        max_facts: int = 10,
        max_chunks: int = 5,
    ) -> str:
        """Format mixed memory content in a consistent block."""
        lines = [title, f"Summary: {summary or 'N/A'}"]
        if chunks:
            chunk_lines = "\n".join(
                f"- {chunk.content}" for chunk in chunks[:max_chunks]
            )
            lines.append("Chunks:\n" + (chunk_lines or "None"))
        if triples:
            triple_lines = "\n".join(f"- {t}" for t in triples[:max_triples])
            lines.append("Knowledge Triples:\n" + (triple_lines or "None"))
        if facts:
            fact_lines = "\n".join(
                f"- {getattr(fact, 'fact', fact)}" for fact in facts[:max_facts]
            )
            lines.append("Atomic Facts:\n" + (fact_lines or "None"))
        return "\n".join(lines)

    def _ensure_embeddings(self, scope: EvaluationScope) -> None:
        """Warm mixed-memory cache before embedding generation."""
        chart_nodes = self._get_chart_nodes(scope.chart)[:30]
        backward_path, forward_path = self._get_full_path(scope)
        path_nodes = list(backward_path) + [scope.target_node] + list(forward_path)

        seen = set()
        ordered: list[Any] = []
        for node in chart_nodes + path_nodes:
            node_id = str(getattr(node, "id", "") or getattr(node, "name", ""))
            if node_id and node_id not in seen:
                seen.add(node_id)
                ordered.append(node)

        self._prime_mixed_cache(ordered)
        super()._ensure_embeddings(scope)

    def _format_context(self, layers):
        layer_map = {lc.layer: lc.content for lc in layers}
        return COMBINED_CONTEXT_TEMPLATE.format(
            l1_content=layer_map.get(1, "No domain context"),
            l2_content=layer_map.get(2, "No category context"),
            l3_content=layer_map.get(3, "No trace context"),
            l4_content=layer_map.get(4, "No episode context"),
        )

    def _filter_l2_results(self, retrieval_result: HMEMContextResult) -> None:
        """Filter L2 results to exclude node-level mixed entries."""
        l2_results = retrieval_result.results_by_layer.get(2, [])
        if not l2_results:
            return

        filtered = []
        for result in l2_results:
            path_hash = result.metadata.get("path_hash", "")
            if path_hash and path_hash.startswith("chart_node_"):
                continue
            if result.content.lstrip().startswith("Node:"):
                continue
            filtered.append(result)

        retrieval_result.results_by_layer[2] = filtered
        retrieval_result.total_retrieved = sum(
            len(results) for results in retrieval_result.results_by_layer.values()
        )

    def _filter_l4_results(
        self, retrieval_result: HMEMContextResult, node_id: str
    ) -> None:
        """Restrict L4 results to the target node only."""
        l4_results = retrieval_result.results_by_layer.get(4, [])
        if not l4_results:
            return

        filtered = [
            result for result in l4_results if result.metadata.get("node_id") == node_id
        ]
        if filtered:
            retrieval_result.results_by_layer[4] = filtered
        else:
            retrieval_result.results_by_layer[4] = []

        retrieval_result.total_retrieved = sum(
            len(results) for results in retrieval_result.results_by_layer.values()
        )

    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """Build context with similarity thresholds for L2/L3 and L2 filtering."""
        if not query:
            query = self._build_query_from_node(scope.target_node)

        if self.auto_embed:
            self._ensure_embeddings(scope)

        project_id = self._get_project_id(scope)

        retrieval_result = self.retriever.retrieve(
            query=query,
            project_id=project_id,
            chart_id=str(scope.chart.id),
            node_id=str(scope.target_node.id),
            top_k_per_layer=self.top_k_per_layer,
            similarity_thresholds={
                2: self.l2_similarity_threshold,
                3: self.l3_similarity_threshold,
            },
        )
        self._filter_l2_results(retrieval_result)
        self._filter_l4_results(retrieval_result, str(scope.target_node.id))

        layers = self._build_layer_contexts(scope, retrieval_result)
        context_string = self._format_context(layers)

        return ContextResult(
            strategy=self.strategy_type,
            context_string=context_string,
            layers=layers,
            triples=[],
            facts=[],
            metadata={
                "target_node_id": str(scope.target_node.id),
                "target_node_name": scope.target_node.name,
                "chart_id": str(scope.chart.id),
                "query": query,
                "total_retrieved": retrieval_result.total_retrieved,
                "embedding_model": self.embedding_model,
                "includes_target_description": True,
                "routing_path": retrieval_result.routing_path,
                "retrieval_per_layer": {
                    layer: len(results)
                    for layer, results in retrieval_result.results_by_layer.items()
                },
                "similarity_thresholds": {
                    "l2": self.l2_similarity_threshold,
                    "l3": self.l3_similarity_threshold,
                },
            },
        )

    def _build_episode_content(self, scope: EvaluationScope) -> str:
        """Build L4 episode content using mixed structural memory."""
        node = scope.target_node
        parts = [f"Node: {node.name}", f"Description: {node.description or 'N/A'}"]
        mixed = self._get_node_mixed_memory(node)
        parts.append(
            self._format_mixed_memory_block(
                "Mixed Memory:",
                mixed["summary"],
                mixed["triples"],
                mixed["facts"],
                chunks=mixed["chunks"],
            )
        )

        return "\n".join(parts)

    def _build_category_entries(self, scope: EvaluationScope) -> list[tuple[str, str]]:
        """
        Build L2 entries using mixed memory for chart nodes and path snippets.

        Keeps chart-level overview entries, then adds mixed memory for nodes and
        path snippets to capture inter-node transitions.
        """
        entries = super()._build_category_entries(scope)

        chart_nodes = self._get_chart_nodes(scope.chart)
        max_nodes = 30
        for node in chart_nodes[:max_nodes]:
            node_name = getattr(node, "name", "") or "Unnamed"
            key = f"chart_node_{self._slugify(node_name)}"
            mixed = self._get_node_mixed_memory(node)
            content = self._format_mixed_memory_block(
                f"Node: {node_name}",
                mixed["summary"],
                mixed["triples"],
                mixed["facts"],
                chunks=None,
            )
            entries.append((key, content))

        return entries

    def _build_trace_entries(
        self,
        scope: EvaluationScope,
        backward_path: list[Any],
        forward_path: list[Any],
    ) -> list[tuple[str, str]]:
        """
        Build L3 entries following H-MEM structure, augmented with mixed memory.

        Includes:
        - Node entries (mixed memory summary/triples/facts)
        - Path snippets (summary only, H-MEM style)
        - Milestones (from H-MEM heuristic)
        """
        entries: list[tuple[str, str]] = []
        full_path = list(backward_path) + [scope.target_node] + list(forward_path)
        if not full_path:
            return entries

        path_id = compute_path_hash(full_path)

        summaries: list[str] = []
        for idx, node in enumerate(full_path):
            node_name = getattr(node, "name", "") or f"node_{idx + 1}"
            key = f"{path_id}_node_{idx + 1}_{self._slugify(node_name)}"
            mixed = self._get_node_mixed_memory(node)
            summaries.append(mixed["summary"])
            content = self._format_mixed_memory_block(
                f"Node: {node_name}",
                mixed["summary"],
                mixed["triples"],
                mixed["facts"],
                chunks=None,
            )
            entries.append((key, content))

        for window_size in (2, 3):
            if len(full_path) < window_size:
                continue
            for i in range(len(full_path) - window_size + 1):
                snippet_nodes = full_path[i : i + window_size]
                snippet_names = " -> ".join(
                    getattr(node, "name", "") or f"Node {i + 1}"
                    for node in snippet_nodes
                )
                snippet_summaries = [
                    self._get_node_mixed_memory(node)["summary"]
                    for node in snippet_nodes
                ]
                summary = "; ".join(s for s in snippet_summaries if s)

                key = f"{path_id}_path_{window_size}_{i + 1}"
                content = self._format_mixed_memory_block(
                    f"Path snippet: {snippet_names}",
                    summary or "N/A",
                    triples=[],
                    facts=[],
                    chunks=None,
                    max_facts=12,
                )
                entries.append((key, content))

        milestones = self._extract_path_milestones(full_path, summaries)
        for idx, milestone in enumerate(milestones, 1):
            key = f"{path_id}_milestone_{idx}"
            entries.append((key, f"Milestone: {milestone}"))

        return entries

    @property
    def requires_llm(self) -> bool:
        """Combined strategy relies on LLM extraction for mixed memory."""
        return True
