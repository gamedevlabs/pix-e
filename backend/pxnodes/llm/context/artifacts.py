"""
Artifact inventory for context strategies.

Stores precomputed artifacts (facts, triples, summaries, etc.) with change hashes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Optional

import logfire

from pxnodes.llm.context.change_detection import compute_node_content_hash
from pxnodes.llm.context.shared.prompts import (
    ATOMIC_FACT_EXTRACTION_PROMPT,
    KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT,
)
from pxnodes.llm.context.structural_memory.chunks import extract_chunks
from pxnodes.llm.context.structural_memory.facts import (
    extract_atomic_facts,
    extract_atomic_facts_async,
    parse_atomic_facts,
)
from pxnodes.llm.context.structural_memory.summaries import (
    SUMMARY_EXTRACTION_PROMPT,
    create_fallback_summary,
    extract_summary,
    extract_summary_async,
)
from pxnodes.llm.context.structural_memory.triples import (
    extract_edge_triples,
    extract_llm_triples_only,
    extract_llm_triples_only_async,
    parse_llm_triples,
)
from pxnodes.models import ContextArtifact, PxNode


SCOPE_NODE = "node"
SCOPE_CHART = "chart"
SCOPE_PATH = "path"
SCOPE_CONCEPT = "concept"
SCOPE_PILLAR = "pillar"

ARTIFACT_RAW_TEXT = "raw_text"
ARTIFACT_CHUNKS = "chunks"
ARTIFACT_SUMMARY = "summary"
ARTIFACT_FACTS = "facts"
ARTIFACT_TRIPLES = "triples"
ARTIFACT_EDGE_TRIPLES = "edge_triples"
ARTIFACT_CHART_OVERVIEW = "chart_overview"
ARTIFACT_NODE_LIST = "node_list"
ARTIFACT_CHART_PACING = "chart_pacing_summary"
ARTIFACT_CHART_MECHANICS = "chart_mechanics"
ARTIFACT_CHART_NARRATIVE = "chart_narrative_summary"
ARTIFACT_PATH_SUMMARY = "path_summary"
ARTIFACT_PATH_SNIPPET = "path_snippet"
ARTIFACT_MILESTONE = "milestone"


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def _first_sentence(text: str, limit: int = 200) -> str:
    if not text:
        return "N/A"
    sentence = text.split(".")[0].strip()
    return sentence[:limit] if sentence else text[:limit]


def compute_text_source_hash(parts: Iterable[str]) -> str:
    joined = "\n".join(part or "" for part in parts)
    return _hash_text(joined)


def compute_path_source_hash(
    chart_id: str, node_ids: list[str], node_hashes: list[str]
) -> str:
    payload = {
        "chart_id": chart_id,
        "node_ids": node_ids,
        "node_hashes": node_hashes,
    }
    return _hash_payload(payload)


class ArtifactInventory:
    def __init__(
        self,
        llm_provider: Optional[Any] = None,
        allow_llm_summaries: bool = True,
    ):
        self.llm_provider = llm_provider
        self.allow_llm_summaries = allow_llm_summaries

    def get_or_build_node_artifacts(
        self,
        chart: Any,
        nodes: list[PxNode],
        artifact_types: list[str],
    ) -> dict[str, list[ContextArtifact]]:
        results: dict[str, list[ContextArtifact]] = {}
        to_build: list[tuple[PxNode, str, str]] = []

        for node in nodes:
            node_id = str(node.id)
            source_hash = compute_node_content_hash(node, chart)
            entries: list[ContextArtifact] = []
            existing = ContextArtifact.objects.filter(
                scope_type=SCOPE_NODE,
                scope_id=node_id,
                artifact_type__in=artifact_types,
                chart=chart,
            )
            existing_map = {entry.artifact_type: entry for entry in existing}

            for artifact_type in artifact_types:
                entry = existing_map.get(artifact_type)
                if entry and entry.source_hash == source_hash:
                    entries.append(entry)
                else:
                    to_build.append((node, artifact_type, source_hash))
            results[node_id] = entries

        if not to_build:
            return results

        try:
            import asyncio

            async def run_parallel() -> list[Any]:
                tasks = [
                    self._build_node_artifact_async(node, artifact_type, chart)
                    for node, artifact_type, _ in to_build
                ]
                return await asyncio.gather(*tasks, return_exceptions=True)

            contents = asyncio.run(run_parallel())
        except RuntimeError:
            contents = [
                self._build_node_artifact(node, artifact_type)
                for node, artifact_type, _ in to_build
            ]

        for (node, artifact_type, source_hash), content in zip(to_build, contents):
            if isinstance(content, Exception):
                content = self._build_node_artifact(node, artifact_type)
            entry = self._upsert_artifact(
                scope_type=SCOPE_NODE,
                scope_id=str(node.id),
                artifact_type=artifact_type,
                source_hash=source_hash,
                content=content,
                chart=chart,
                node=node,
            )
            results[str(node.id)].append(entry)

        return results

    def get_or_build_concept_artifacts(
        self,
        concept_id: str,
        concept_text: str,
        artifact_types: list[str],
        project_id: str = "",
    ) -> list[ContextArtifact]:
        source_hash = compute_text_source_hash([concept_text])
        entries: list[ContextArtifact] = []
        to_build: list[str] = []

        existing = ContextArtifact.objects.filter(
            scope_type=SCOPE_CONCEPT,
            scope_id=concept_id,
            artifact_type__in=artifact_types,
            project_id=project_id,
        )
        existing_map = {entry.artifact_type: entry for entry in existing}

        for artifact_type in artifact_types:
            entry = existing_map.get(artifact_type)
            if entry and entry.source_hash == source_hash:
                entries.append(entry)
            else:
                to_build.append(artifact_type)

        if to_build:
            entries.extend(
                self._build_text_artifacts_parallel(
                    scope_type=SCOPE_CONCEPT,
                    scope_id=concept_id,
                    source_hash=source_hash,
                    title="Game Concept",
                    text=concept_text,
                    artifact_types=to_build,
                    project_id=project_id,
                )
            )

        return entries

    def get_or_build_pillar_artifacts(
        self,
        pillar_id: str,
        pillar_name: str,
        pillar_description: str,
        artifact_types: list[str],
        project_id: str = "",
    ) -> list[ContextArtifact]:
        source_hash = compute_text_source_hash([pillar_name, pillar_description])
        entries: list[ContextArtifact] = []
        to_build: list[str] = []

        existing = ContextArtifact.objects.filter(
            scope_type=SCOPE_PILLAR,
            scope_id=pillar_id,
            artifact_type__in=artifact_types,
            project_id=project_id,
        )
        existing_map = {entry.artifact_type: entry for entry in existing}

        for artifact_type in artifact_types:
            entry = existing_map.get(artifact_type)
            if entry and entry.source_hash == source_hash:
                entries.append(entry)
            else:
                to_build.append(artifact_type)

        if to_build:
            entries.extend(
                self._build_text_artifacts_parallel(
                    scope_type=SCOPE_PILLAR,
                    scope_id=pillar_id,
                    source_hash=source_hash,
                    title=pillar_name or "Pillar",
                    text=pillar_description,
                    artifact_types=to_build,
                    project_id=project_id,
                )
            )

        return entries

    def get_or_build_chart_artifacts(
        self,
        chart: Any,
        artifact_types: list[str],
    ) -> list[ContextArtifact]:
        nodes = self._get_chart_nodes(chart)
        node_names = [getattr(node, "name", "") for node in nodes if node]
        edges = self._get_chart_edges(chart)
        edge_pairs = []
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
                edge_pairs.append(f"{source_name}->{target_name}")
        node_hashes = [
            compute_node_content_hash(node, chart) for node in nodes if node
        ]
        chart_mechanics = self._get_chart_component_names(nodes)
        chart_pacing_summary = self._build_chart_pacing_summary(nodes, edges)
        chart_narrative_summary = self._build_chart_narrative_summary(nodes, edges)
        overview = {
            "name": getattr(chart, "name", ""),
            "description": getattr(chart, "description", ""),
            "total_nodes": len(nodes),
        }
        node_list = node_names
        source_hash = compute_text_source_hash(
            [
                overview["name"],
                overview["description"],
                ",".join(node_list),
                ",".join(edge_pairs),
                ",".join(node_hashes),
                ",".join(sorted(chart_mechanics)),
                chart_pacing_summary,
                chart_narrative_summary,
            ]
        )
        entries: list[ContextArtifact] = []
        for artifact_type in artifact_types:
            if artifact_type == ARTIFACT_CHART_OVERVIEW:
                content = overview
                builder = lambda c=content: c
            elif artifact_type == ARTIFACT_NODE_LIST:
                content = node_list
                builder = lambda c=content: c
            elif artifact_type == ARTIFACT_EDGE_TRIPLES:
                def build_edge_triples(payload_edges=edges) -> list[dict[str, Any]]:
                    triples_payload = []
                    for edge in payload_edges:
                        for triple in extract_edge_triples(edge):
                            source_node_id = (
                                str(edge.source.content.id)
                                if edge.source and edge.source.content
                                else ""
                            )
                            target_node_id = (
                                str(edge.target.content.id)
                                if edge.target and edge.target.content
                                else ""
                            )
                            triples_payload.append(
                                {
                                    "head": triple.head,
                                    "relation": triple.relation,
                                    "tail": triple.tail,
                                    "text": str(triple),
                                    "source_node_id": source_node_id,
                                    "target_node_id": target_node_id,
                                }
                            )
                    return triples_payload

                builder = build_edge_triples
            elif artifact_type == ARTIFACT_CHART_PACING:
                builder = lambda c=chart_pacing_summary: c
            elif artifact_type == ARTIFACT_CHART_MECHANICS:
                builder = lambda c=list(sorted(chart_mechanics)): c
            elif artifact_type == ARTIFACT_CHART_NARRATIVE:
                builder = lambda c=chart_narrative_summary: c
            else:
                combined = "\n".join(
                    [
                        f"Chart: {overview['name']}",
                        f"Description: {overview['description']}",
                        f"Nodes: {', '.join(node_list)}",
                    ]
                )
                content = self._build_text_artifact(
                    title=overview["name"] or "Chart",
                    text=combined,
                    artifact_type=artifact_type,
                )
                builder = lambda c=content: c
            entry = self._get_or_build_artifact(
                scope_type=SCOPE_CHART,
                scope_id=str(getattr(chart, "id", "")),
                artifact_type=artifact_type,
                source_hash=source_hash,
                chart=chart,
                builder=builder,
            )
            entries.append(entry)
        return entries

    def get_or_build_path_artifacts(
        self,
        chart: Any,
        path_nodes: list[PxNode],
        artifact_types: list[str],
    ) -> list[ContextArtifact]:
        node_ids = [str(node.id) for node in path_nodes]
        node_hashes = [compute_node_content_hash(node, chart) for node in path_nodes]
        scope_id = hashlib.sha256(">".join(node_ids).encode()).hexdigest()
        source_hash = compute_path_source_hash(
            str(getattr(chart, "id", "")), node_ids, node_hashes
        )
        entries: list[ContextArtifact] = []
        for artifact_type in artifact_types:
            entry = self._get_or_build_artifact(
                scope_type=SCOPE_PATH,
                scope_id=scope_id,
                artifact_type=artifact_type,
                source_hash=source_hash,
                chart=chart,
                metadata={"node_ids": node_ids},
                builder=lambda t=artifact_type: self._build_path_artifact(
                    path_nodes, t
                ),
            )
            entries.append(entry)
        return entries

    def _get_or_build_artifact(
        self,
        scope_type: str,
        scope_id: str,
        artifact_type: str,
        source_hash: str,
        builder: Any,
        chart: Optional[Any] = None,
        node: Optional[PxNode] = None,
        project_id: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ContextArtifact:
        entry = ContextArtifact.objects.filter(
            scope_type=scope_type,
            scope_id=scope_id,
            artifact_type=artifact_type,
            chart=chart,
            project_id=project_id,
        ).first()

        if entry and entry.source_hash == source_hash:
            return entry

        content = builder() if callable(builder) else builder
        content_hash = _hash_payload(content)
        payload = metadata or {}

        if entry:
            entry.content = content
            entry.content_hash = content_hash
            entry.source_hash = source_hash
            entry.metadata = payload
            entry.node = node
            entry.chart = chart
            entry.save(
                update_fields=[
                    "content",
                    "content_hash",
                    "source_hash",
                    "metadata",
                    "node",
                    "chart",
                    "updated_at",
                ]
            )
            return entry

        return ContextArtifact.objects.create(
            scope_type=scope_type,
            scope_id=scope_id,
            artifact_type=artifact_type,
            node=node,
            chart=chart,
            project_id=project_id,
            content=content,
            content_hash=content_hash,
            source_hash=source_hash,
            metadata=payload,
        )

    def _upsert_artifact(
        self,
        scope_type: str,
        scope_id: str,
        artifact_type: str,
        source_hash: str,
        content: Any,
        chart: Optional[Any] = None,
        node: Optional[PxNode] = None,
        project_id: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> ContextArtifact:
        entry = ContextArtifact.objects.filter(
            scope_type=scope_type,
            scope_id=scope_id,
            artifact_type=artifact_type,
            chart=chart,
            project_id=project_id,
        ).first()

        content_hash = _hash_payload(content)
        payload = metadata or {}

        if entry:
            entry.content = content
            entry.content_hash = content_hash
            entry.source_hash = source_hash
            entry.metadata = payload
            entry.node = node
            entry.chart = chart
            entry.save(
                update_fields=[
                    "content",
                    "content_hash",
                    "source_hash",
                    "metadata",
                    "node",
                    "chart",
                    "updated_at",
                ]
            )
            return entry

        return ContextArtifact.objects.create(
            scope_type=scope_type,
            scope_id=scope_id,
            artifact_type=artifact_type,
            node=node,
            chart=chart,
            project_id=project_id,
            content=content,
            content_hash=content_hash,
            source_hash=source_hash,
            metadata=payload,
        )

    def _build_node_artifact(self, node: PxNode, artifact_type: str) -> Any:
        if artifact_type == ARTIFACT_RAW_TEXT:
            parts = [f"Node: {node.name}", node.description or ""]
            components = node.components.select_related("definition").all()
            for comp in components:
                def_name = getattr(comp.definition, "name", "")
                value = getattr(comp, "value", "")
                parts.append(f"{def_name}: {value}")
            return "\n".join(p for p in parts if p)

        if artifact_type == ARTIFACT_CHUNKS:
            return [
                {"content": chunk.content, "source": chunk.source}
                for chunk in extract_chunks(node)
            ]

        if artifact_type == ARTIFACT_SUMMARY:
            if self.llm_provider and self.allow_llm_summaries:
                with logfire.span(
                    "artifact.summary.node",
                    node_id=str(node.id),
                    node_name=getattr(node, "name", ""),
                ):
                    summary = extract_summary(node, self.llm_provider)
                if summary:
                    return summary.content
            return create_fallback_summary(node).content

        if artifact_type == ARTIFACT_FACTS:
            if not self.llm_provider:
                return []
            with logfire.span(
                "artifact.facts.node",
                node_id=str(node.id),
                node_name=getattr(node, "name", ""),
            ):
                facts = extract_atomic_facts(node, self.llm_provider)
            return [
                {"fact": fact.fact, "source_field": fact.source_field} for fact in facts
            ]

        if artifact_type == ARTIFACT_TRIPLES:
            if not self.llm_provider:
                return []
            with logfire.span(
                "artifact.triples.node",
                node_id=str(node.id),
                node_name=getattr(node, "name", ""),
            ):
                triples = extract_llm_triples_only(node, self.llm_provider)
            return [
                {
                    "head": triple.head,
                    "relation": triple.relation,
                    "tail": triple.tail,
                    "text": str(triple),
                }
                for triple in triples
            ]

        return ""

    async def _build_node_artifact_async(
        self, node: PxNode, artifact_type: str, chart: Any
    ) -> Any:
        node_id = str(node.id)
        node_name = getattr(node, "name", "")

        if artifact_type == ARTIFACT_SUMMARY:
            if self.llm_provider and self.allow_llm_summaries:
                with logfire.span(
                    "artifact.summary.node",
                    node_id=node_id,
                    node_name=node_name,
                ):
                    summary = await extract_summary_async(node, self.llm_provider)
                    return summary.content if summary else ""
            return create_fallback_summary(node).content

        if artifact_type == ARTIFACT_FACTS:
            if not self.llm_provider:
                return []
            with logfire.span(
                "artifact.facts.node",
                node_id=node_id,
                node_name=node_name,
            ):
                facts = await extract_atomic_facts_async(
                    node,
                    self.llm_provider,
                    force_regenerate=True,
                    chart_id=str(getattr(chart, "id", "")),
                )
            return [
                {"fact": fact.fact, "source_field": fact.source_field} for fact in facts
            ]

        if artifact_type == ARTIFACT_TRIPLES:
            if not self.llm_provider:
                return []
            with logfire.span(
                "artifact.triples.node",
                node_id=node_id,
                node_name=node_name,
            ):
                triples = await extract_llm_triples_only_async(node, self.llm_provider)
            return [
                {
                    "head": triple.head,
                    "relation": triple.relation,
                    "tail": triple.tail,
                    "text": str(triple),
                }
                for triple in triples
            ]

        if artifact_type == ARTIFACT_CHUNKS:
            import asyncio

            chunks = await asyncio.to_thread(extract_chunks, node)
            return [
                {"content": chunk.content, "source": chunk.source} for chunk in chunks
            ]

        if artifact_type == ARTIFACT_RAW_TEXT:
            return self._build_node_artifact(node, artifact_type)

        return ""

    def _build_path_artifact(self, nodes: list[PxNode], artifact_type: str) -> Any:
        if artifact_type == ARTIFACT_PATH_SUMMARY:
            summaries = self._summarize_nodes_parallel(nodes)
            return [f"{node.name}: {summary}" for node, summary in zip(nodes, summaries)]
        return []

    def _build_text_artifact(self, title: str, text: str, artifact_type: str) -> Any:
        if artifact_type == ARTIFACT_RAW_TEXT:
            return text
        if artifact_type == ARTIFACT_SUMMARY:
            return self._summarize_text(title, text)
        if artifact_type == ARTIFACT_FACTS:
            return self._extract_facts(title, text)
        if artifact_type == ARTIFACT_TRIPLES:
            return self._extract_triples(title, text)
        return ""

    def _build_text_artifacts_parallel(
        self,
        scope_type: str,
        scope_id: str,
        source_hash: str,
        title: str,
        text: str,
        artifact_types: list[str],
        project_id: str = "",
    ) -> list[ContextArtifact]:
        if not artifact_types:
            return []

        try:
            import asyncio

            async def run_parallel() -> list[Any]:
                tasks = [
                    asyncio.to_thread(self._build_text_artifact, title, text, t)
                    for t in artifact_types
                ]
                return await asyncio.gather(*tasks, return_exceptions=True)

            contents = asyncio.run(run_parallel())
        except RuntimeError:
            contents = [
                self._build_text_artifact(title, text, t) for t in artifact_types
            ]

        entries: list[ContextArtifact] = []
        for artifact_type, content in zip(artifact_types, contents):
            if isinstance(content, Exception):
                content = self._build_text_artifact(title, text, artifact_type)
            entry = self._upsert_artifact(
                scope_type=scope_type,
                scope_id=scope_id,
                artifact_type=artifact_type,
                source_hash=source_hash,
                content=content,
                project_id=project_id,
            )
            entries.append(entry)

        return entries

    def _summarize_text(self, title: str, text: str) -> str:
        if not text:
            return "N/A"
        if not self.llm_provider or not self.allow_llm_summaries:
            return _first_sentence(text)
        prompt = SUMMARY_EXTRACTION_PROMPT.format(
            title=title,
            description=text,
            components="- No components attached",
        )
        try:
            with logfire.span("artifact.summary.text", title=title):
                response = self.llm_provider.generate(
                    prompt, operation="text_summary"
                )
            return response.strip() or _first_sentence(text)
        except Exception:
            return _first_sentence(text)

    def _extract_facts(self, title: str, text: str) -> list[dict[str, Any]]:
        if not text or not self.llm_provider:
            return []
        prompt = ATOMIC_FACT_EXTRACTION_PROMPT.format(
            title=title,
            description=text,
            components="- No components attached",
        )
        try:
            with logfire.span("artifact.facts.text", title=title):
                response = self.llm_provider.generate(prompt, operation="text_facts")
            return [
                {"fact": fact, "source_field": "text"}
                for fact in parse_atomic_facts(response)
            ]
        except Exception:
            return []

    def _extract_triples(self, title: str, text: str) -> list[dict[str, Any]]:
        if not text or not self.llm_provider:
            return []
        prompt = KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT.format(
            title=title,
            description=text,
            components="- No components attached",
        )
        try:
            with logfire.span("artifact.triples.text", title=title):
                response = self.llm_provider.generate(
                    prompt, operation="text_triples"
                )
            triples = parse_llm_triples(response)
            return [
                {
                    "head": triple.head,
                    "relation": triple.relation,
                    "tail": triple.tail,
                    "text": str(triple),
                }
                for triple in triples
            ]
        except Exception:
            return []

    def _get_chart_nodes(self, chart: Any) -> list[PxNode]:
        containers = getattr(chart, "containers", None)
        if not containers:
            return []
        if hasattr(containers, "filter"):
            containers = containers.filter(content__isnull=False)
        container_list = (
            containers.all() if hasattr(containers, "all") else list(containers)
        )
        return [c.content for c in container_list if getattr(c, "content", None)]

    def _get_chart_edges(self, chart: Any) -> list[Any]:
        edges = getattr(chart, "edges", None)
        if not edges:
            return []
        if hasattr(edges, "select_related"):
            edges = edges.select_related("source__content", "target__content")
        return edges.all() if hasattr(edges, "all") else list(edges)

    def _get_chart_component_names(self, nodes: list[PxNode]) -> set[str]:
        component_names: set[str] = set()
        for node in nodes:
            components = getattr(node, "components", None)
            comp_list = (
                components.all() if components and hasattr(components, "all") else []
            )
            for comp in comp_list:
                def_name = getattr(getattr(comp, "definition", None), "name", "")
                if def_name and def_name != "Planned Time to Complete":
                    component_names.add(def_name)
        return component_names

    def _build_chart_pacing_summary(self, nodes: list[PxNode], edges: list[Any]) -> str:
        if not nodes:
            return ""
        node_lines = []
        for node in nodes[:30]:
            name = getattr(node, "name", "") or "Unnamed"
            desc = getattr(node, "description", "") or ""
            if desc:
                node_lines.append(f"{name}: {desc}")
        if not node_lines:
            return ""
        edge_lines = self._format_edge_lines(edges)
        text = "\n".join(node_lines)
        if edge_lines:
            text += "\n\nChart Edges:\n" + "\n".join(edge_lines)
        summary = self._summarize_text("Chart Pacing", text)
        return f"Chart Pacing Summary:\n{summary}" if summary else ""

    def _build_chart_narrative_summary(
        self, nodes: list[PxNode], edges: list[Any]
    ) -> str:
        node_lines = []
        for node in nodes[:30]:
            name = getattr(node, "name", "") or "Unnamed"
            desc = getattr(node, "description", "") or ""
            if desc:
                node_lines.append(f"{name}: {desc}")
        if not node_lines:
            return ""
        edge_lines = self._format_edge_lines(edges)
        text = "\n".join(node_lines)
        if edge_lines:
            text += "\n\nChart Edges:\n" + "\n".join(edge_lines)
        summary = self._summarize_text("Chart Narrative Arc", text)
        return f"Chart Narrative Arc:\n{summary}" if summary else ""

    def _format_edge_lines(self, edges: list[Any]) -> list[str]:
        edge_lines = []
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
                edge_lines.append(f"{source_name} -> {target_name}")
        return edge_lines

    def _summarize_nodes_parallel(self, nodes: list[PxNode]) -> list[str]:
        if not nodes:
            return []
        if not self.llm_provider or not self.allow_llm_summaries or len(nodes) == 1:
            summaries: list[str] = []
            for node in nodes:
                if not self.llm_provider or not self.allow_llm_summaries:
                    summaries.append(create_fallback_summary(node).content)
                else:
                    summary = extract_summary(node, self.llm_provider)
                    summaries.append(summary.content if summary else "")
            return summaries

        try:
            import asyncio

            async def run_parallel() -> list[str]:
                tasks = [
                    asyncio.to_thread(extract_summary, node, self.llm_provider)
                    for node in nodes
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                summaries: list[str] = []
                for node, result in zip(nodes, results):
                    if isinstance(result, Exception):
                        summaries.append(create_fallback_summary(node).content)
                    else:
                        summaries.append(result.content if result else "")
                return summaries

            return asyncio.run(run_parallel())
        except RuntimeError:
            summaries: list[str] = []
            for node in nodes:
                summary = extract_summary(node, self.llm_provider)
                summaries.append(summary.content if summary else "")
            return summaries
