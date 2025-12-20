"""
H-MEM strategy for SPARC.

Implements a hierarchical memory structure inspired by Sun & Zeng (2025):
Domain -> Category -> Trace -> Episode. Retrieval follows top-down routing.
"""

import asyncio
import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from llm.providers.manager import ModelManager
from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
from sparc.llm.context.hmem.prompts import (
    ASPECT_SUMMARY_PROMPT,
    DOMAIN_SUMMARY_PROMPT,
)
from sparc.llm.context.registry import ContextStrategyRegistry
from sparc.llm.context.strategy import BaseContextStrategy
from sparc.llm.context.types import (
    AspectContext,
    AspectContextResult,
    ContextStrategyType,
)
from sparc.llm.schemas.v2.router import RouterResponse

logger = logging.getLogger(__name__)


ASPECT_DESCRIPTIONS = {
    "player_experience": "emotions, pacing, tension, player feelings, engagement",
    "theme": "themes, message, tone, motifs, underlying meaning",
    "purpose": "design intent, goals for the project, motivation",
    "gameplay": "core mechanics, loops, systems, moment-to-moment play",
    "goals_challenges_rewards": "objectives, challenges, rewards, progression",
    "place": "setting, world, locations, environment, atmosphere",
    "story_narrative": "plot, story beats, narrative structure, characters",
    "unique_features": "distinctive mechanics, innovation, differentiators",
    "art_direction": "visual style, aesthetics, audio mood, presentation",
    "opportunities_risks": "risks, constraints, market fit, mitigation ideas",
}


@dataclass
class MemoryNode:
    """Memory node with optional embedding."""

    text: str
    embedding: Optional[List[float]] = None


@ContextStrategyRegistry.register(ContextStrategyType.HMEM)
class HMemContextStrategy(BaseContextStrategy):
    """Hierarchical memory strategy for SPARC aspects."""

    strategy_type = ContextStrategyType.HMEM

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        model_id: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        max_chunk_chars: int = 800,
        top_k_traces: int = 6,
        max_parallel_aspects: int = 5,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.model_manager = model_manager
        self.model_id = model_id
        self.embedding_model = embedding_model
        self.max_chunk_chars = max_chunk_chars
        self.top_k_traces = top_k_traces
        self.max_parallel_aspects = max_parallel_aspects
        self._embedder: Optional[OpenAIEmbeddingGenerator] = None

    async def build_aspect_contexts(
        self,
        data: Dict[str, Any],
        target_aspects: Iterable[str],
        router_response: Optional[RouterResponse] = None,
    ) -> AspectContextResult:
        game_text = data.get("game_text", "")
        if not game_text:
            return AspectContextResult(strategy=self.strategy_type)

        domain_task = asyncio.to_thread(self._build_domain_summary, game_text)
        aspects_task = self._build_aspect_summaries_async(game_text, target_aspects)
        domain_summary, aspect_summaries = await asyncio.gather(
            domain_task, aspects_task
        )
        traces = self._build_traces(game_text)

        self._attach_embeddings([domain_summary])
        self._attach_embeddings(list(aspect_summaries.values()))
        self._attach_embeddings(traces)

        semaphore = asyncio.Semaphore(self.max_parallel_aspects)

        async def build_aspect(aspect_name: str) -> tuple[str, AspectContext]:
            async with semaphore:
                return await asyncio.to_thread(
                    self._build_aspect_context,
                    aspect_name,
                    domain_summary,
                    aspect_summaries,
                    traces,
                )

        tasks = [build_aspect(aspect_name) for aspect_name in target_aspects]
        results = await asyncio.gather(*tasks)
        contexts = {aspect_name: context for aspect_name, context in results}

        return AspectContextResult(
            strategy=self.strategy_type,
            contexts=contexts,
            metadata={"trace_count": len(traces)},
        )

    def _build_domain_summary(self, game_text: str) -> MemoryNode:
        if not self.model_manager or not self.model_id:
            return MemoryNode(text=self._fallback_domain_summary(game_text))
        prompt = DOMAIN_SUMMARY_PROMPT.format(game_text=game_text)
        summary = self._generate_text(prompt)
        return MemoryNode(text=summary or self._fallback_domain_summary(game_text))

    def _build_aspect_summaries(
        self,
        game_text: str,
        target_aspects: Iterable[str],
    ) -> Dict[str, MemoryNode]:
        summaries: Dict[str, MemoryNode] = {}
        for aspect_name in target_aspects:
            aspect_description = ASPECT_DESCRIPTIONS.get(aspect_name, aspect_name)
            if not self.model_manager or not self.model_id:
                summaries[aspect_name] = MemoryNode(
                    text=f"{aspect_name}: {aspect_description}"
                )
                continue
            prompt = ASPECT_SUMMARY_PROMPT.format(
                aspect_name=aspect_name,
                aspect_description=aspect_description,
                game_text=game_text,
            )
            summary = self._generate_text(prompt)
            summaries[aspect_name] = MemoryNode(
                text=summary or f"{aspect_name}: {aspect_description}"
            )
        return summaries

    async def _build_aspect_summaries_async(
        self,
        game_text: str,
        target_aspects: Iterable[str],
    ) -> Dict[str, MemoryNode]:
        if not self.model_manager or not self.model_id:
            return self._build_aspect_summaries(game_text, target_aspects)

        semaphore = asyncio.Semaphore(self.max_parallel_aspects)

        async def build_summary(aspect_name: str) -> tuple[str, MemoryNode]:
            async with semaphore:
                return await asyncio.to_thread(
                    self._build_aspect_summary, game_text, aspect_name
                )

        tasks = [build_summary(aspect_name) for aspect_name in target_aspects]
        results = await asyncio.gather(*tasks)
        return dict(results)

    def _build_aspect_summary(
        self, game_text: str, aspect_name: str
    ) -> tuple[str, MemoryNode]:
        aspect_description = ASPECT_DESCRIPTIONS.get(aspect_name, aspect_name)
        prompt = ASPECT_SUMMARY_PROMPT.format(
            aspect_name=aspect_name,
            aspect_description=aspect_description,
            game_text=game_text,
        )
        summary = self._generate_text(prompt)
        return (
            aspect_name,
            MemoryNode(text=summary or f"{aspect_name}: {aspect_description}"),
        )

    def _build_traces(self, game_text: str) -> List[MemoryNode]:
        chunks = self._chunk_text(game_text)
        return [MemoryNode(text=chunk) for chunk in chunks]

    def _chunk_text(self, text: str) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks: List[str] = []
        for paragraph in paragraphs:
            if len(paragraph) <= self.max_chunk_chars:
                chunks.append(paragraph)
                continue
            current: List[str] = []
            current_len = 0
            for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
                if not sentence:
                    continue
                if current_len + len(sentence) > self.max_chunk_chars and current:
                    chunks.append(" ".join(current))
                    current = []
                    current_len = 0
                current.append(sentence)
                current_len += len(sentence) + 1
            if current:
                chunks.append(" ".join(current))
        return chunks

    def _attach_embeddings(self, nodes: List[MemoryNode]) -> None:
        if not nodes:
            return
        if not self._embedder:
            try:
                self._embedder = OpenAIEmbeddingGenerator(model=self.embedding_model)
            except Exception as e:
                logger.warning("Embedding generator unavailable: %s", e)
                return

        texts = [node.text for node in nodes]
        try:
            embeddings = self._embedder.generate_embeddings_batch(texts)
        except Exception as e:
            logger.warning("Embedding generation failed: %s", e)
            return

        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding

    def _route_traces(
        self,
        aspect_name: str,
        summary_node: Optional[MemoryNode],
        traces: List[MemoryNode],
    ) -> List[MemoryNode]:
        if not traces:
            return []

        query = ASPECT_DESCRIPTIONS.get(aspect_name, aspect_name)
        summary_text = summary_node.text if summary_node else query

        ranked = self._rank_nodes(summary_text, traces)
        return ranked[: self.top_k_traces]

    def _build_aspect_context(
        self,
        aspect_name: str,
        domain_summary: MemoryNode,
        aspect_summaries: Dict[str, MemoryNode],
        traces: List[MemoryNode],
    ) -> tuple[str, AspectContext]:
        summary_node = aspect_summaries.get(aspect_name)
        selected_traces = self._route_traces(aspect_name, summary_node, traces)
        section = self._format_context_block(
            aspect_name, domain_summary, summary_node, selected_traces
        )
        return (
            aspect_name,
            AspectContext(
                aspect_name=aspect_name,
                extracted_sections=[section] if section else [],
                metadata={
                    "traces_used": len(selected_traces),
                    "strategy": self.strategy_type.value,
                },
            ),
        )

    def _rank_nodes(self, query: str, nodes: List[MemoryNode]) -> List[MemoryNode]:
        if all(node.embedding is None for node in nodes):
            return sorted(
                nodes,
                key=lambda n: self._overlap_score(query, n.text),
                reverse=True,
            )

        query_embedding = None
        if self._embedder:
            try:
                query_embedding = self._embedder.generate_embedding(query)
            except Exception as e:
                logger.warning("Query embedding failed: %s", e)

        if query_embedding is None:
            return sorted(
                nodes,
                key=lambda n: self._overlap_score(query, n.text),
                reverse=True,
            )

        scored = [
            (node, self._cosine_similarity(query_embedding, node.embedding))
            for node in nodes
            if node.embedding is not None
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        ranked = [node for node, _ in scored]

        missing = [node for node in nodes if node.embedding is None]
        if missing:
            missing_sorted = sorted(
                missing,
                key=lambda n: self._overlap_score(query, n.text),
                reverse=True,
            )
            ranked.extend(missing_sorted)

        return ranked

    def _generate_text(self, prompt: str) -> str:
        if not self.model_manager or not self.model_id:
            return ""
        try:
            result = self.model_manager.generate_with_model(
                self.model_id,
                prompt,
                temperature=0.2,
                max_tokens=600,
            )
            return result.text.strip()
        except Exception as e:
            logger.warning("H-MEM generation failed: %s", e)
            return ""

    def _fallback_domain_summary(self, game_text: str) -> str:
        paragraphs = [p.strip() for p in game_text.split("\n") if p.strip()]
        return "\n".join(paragraphs[:2])

    def _overlap_score(self, query: str, text: str) -> int:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        text_tokens = set(re.findall(r"\w+", text.lower()))
        return len(query_tokens.intersection(text_tokens))

    def _cosine_similarity(
        self, vec_a: Optional[List[float]], vec_b: Optional[List[float]]
    ) -> float:
        if vec_a is None or vec_b is None:
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _format_context_block(
        self,
        aspect_name: str,
        domain_summary: MemoryNode,
        aspect_summary: Optional[MemoryNode],
        traces: List[MemoryNode],
    ) -> str:
        if not traces:
            return ""

        sections = [f"[H-MEM] Aspect: {aspect_name}"]
        if domain_summary.text:
            sections.append("\n[L1 DOMAIN]\n" + domain_summary.text)
        if aspect_summary and aspect_summary.text:
            sections.append("\n[L2 CATEGORY]\n" + aspect_summary.text)
        if traces:
            sections.append("\n[L3 TRACE]\n" + "\n".join(node.text for node in traces))
            sections.append(
                "\n[L4 EPISODES]\n" + "\n".join(node.text for node in traces)
            )

        return "\n".join(sections).strip()
