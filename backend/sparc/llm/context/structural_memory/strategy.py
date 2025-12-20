"""
Structural Memory strategy for SPARC.

Implements the mixed memory representation from Zeng et al. (2024):
chunks, atomic facts, knowledge triples, and summaries, with iterative retrieval.
"""

import asyncio
import logging
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from llm.providers.manager import ModelManager
from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
from sparc.llm.context.registry import ContextStrategyRegistry
from sparc.llm.context.strategy import BaseContextStrategy
from sparc.llm.context.structural_memory.prompts import (
    ATOMICS_PROMPT,
    REFINE_QUERY_PROMPT,
    SUMMARY_PROMPT,
    TRIPLES_PROMPT,
)
from sparc.llm.context.types import (
    AspectContext,
    AspectContextResult,
    ContextStrategyType,
)
from sparc.llm.schemas.v2.router import RouterResponse

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """Simple memory unit for structural memory retrieval."""

    kind: str
    text: str
    embedding: Optional[List[float]] = None


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


@ContextStrategyRegistry.register(ContextStrategyType.STRUCTURAL_MEMORY)
class StructuralMemoryContextStrategy(BaseContextStrategy):
    """Mixed structural memory with iterative retrieval for SPARC aspects."""

    strategy_type = ContextStrategyType.STRUCTURAL_MEMORY

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        model_id: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
        retrieval_iterations: int = 2,
        retrieval_top_k: int = 10,
        max_chunk_chars: int = 800,
        max_parallel_aspects: int = 5,
        min_triples: int = 3,
        min_facts: int = 8,
        min_chunks: int = 3,
        max_summary: int = 1,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.model_manager = model_manager
        self.model_id = model_id
        self.embedding_model = embedding_model
        self.retrieval_iterations = retrieval_iterations
        self.retrieval_top_k = retrieval_top_k
        self.max_chunk_chars = max_chunk_chars
        self.max_parallel_aspects = max_parallel_aspects
        self.min_triples = min_triples
        self.min_facts = min_facts
        self.min_chunks = min_chunks
        self.max_summary = max_summary
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

        memory_items = await self._build_memory_items_async(game_text)
        self._attach_embeddings(memory_items)

        semaphore = asyncio.Semaphore(self.max_parallel_aspects)

        async def build_aspect(aspect_name: str) -> tuple[str, AspectContext]:
            async with semaphore:
                return await asyncio.to_thread(
                    self._build_aspect_context, aspect_name, memory_items
                )

        tasks = [build_aspect(aspect_name) for aspect_name in target_aspects]
        results = await asyncio.gather(*tasks)
        contexts = {aspect_name: context for aspect_name, context in results}

        return AspectContextResult(
            strategy=self.strategy_type,
            contexts=contexts,
            metadata={"memory_items": len(memory_items)},
        )

    def _build_base_query(self, aspect_name: str, aspect_description: str) -> str:
        return (
            f"Find information about {aspect_name}: {aspect_description}. "
            "Prefer explicit statements from the game concept."
        )

    async def _build_memory_items_async(self, game_text: str) -> List[MemoryItem]:
        chunks = self._chunk_text(game_text)
        if not self.model_manager or not self.model_id:
            return [MemoryItem(kind="chunk", text=chunk) for chunk in chunks]

        facts_task = asyncio.to_thread(self._extract_atomic_facts, game_text)
        triples_task = asyncio.to_thread(self._extract_triples, game_text)
        summary_task = asyncio.to_thread(self._extract_summary, game_text)
        facts, triples, summary = await asyncio.gather(
            facts_task, triples_task, summary_task
        )

        items: List[MemoryItem] = []
        items.extend([MemoryItem(kind="chunk", text=chunk) for chunk in chunks])
        items.extend([MemoryItem(kind="fact", text=fact) for fact in facts])
        items.extend([MemoryItem(kind="triple", text=triple) for triple in triples])
        if summary:
            items.append(MemoryItem(kind="summary", text=summary))

        return items

    def _build_aspect_context(
        self, aspect_name: str, memory_items: List[MemoryItem]
    ) -> tuple[str, AspectContext]:
        aspect_description = ASPECT_DESCRIPTIONS.get(aspect_name, aspect_name)
        query = self._build_base_query(aspect_name, aspect_description)
        ranked = self._iterative_retrieve(
            aspect_name, query, aspect_description, memory_items
        )
        section = self._format_context_block(aspect_name, ranked)
        return (
            aspect_name,
            AspectContext(
                aspect_name=aspect_name,
                extracted_sections=[section] if section else [],
                metadata={
                    "items_used": len(ranked),
                    "query": query,
                    "strategy": self.strategy_type.value,
                },
            ),
        )

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

    def _extract_atomic_facts(self, text: str) -> List[str]:
        if not self.model_manager or not self.model_id:
            return []
        prompt = ATOMICS_PROMPT.format(game_text=text)
        response = self._generate_text(prompt)
        return self._split_lines(response)

    def _extract_triples(self, text: str) -> List[str]:
        if not self.model_manager or not self.model_id:
            return []
        prompt = TRIPLES_PROMPT.format(game_text=text)
        response = self._generate_text(prompt)
        return self._split_lines(response)

    def _extract_summary(self, text: str) -> str:
        if not self.model_manager or not self.model_id:
            return ""
        prompt = SUMMARY_PROMPT.format(game_text=text)
        return self._generate_text(prompt).strip()

    def _generate_text(self, prompt: str) -> str:
        if not self.model_manager or not self.model_id:
            return ""
        try:
            result = self.model_manager.generate_with_model(
                self.model_id,
                prompt,
                temperature=0.2,
                max_tokens=800,
            )
            return result.text.strip()
        except Exception as e:
            logger.warning("Structural memory generation failed: %s", e)
            return ""

    def _split_lines(self, text: str) -> List[str]:
        lines = []
        for line in text.splitlines():
            cleaned = line.strip().lstrip("-").strip()
            if not cleaned:
                continue
            lines.append(cleaned)
        return lines

    def _attach_embeddings(self, items: List[MemoryItem]) -> None:
        if not items:
            return
        if not self._embedder:
            try:
                self._embedder = OpenAIEmbeddingGenerator(model=self.embedding_model)
            except Exception as e:
                logger.warning("Embedding generator unavailable: %s", e)
                return

        texts = [item.text for item in items]
        try:
            embeddings = self._embedder.generate_embeddings_batch(texts)
        except Exception as e:
            logger.warning("Embedding generation failed: %s", e)
            return

        for item, embedding in zip(items, embeddings):
            item.embedding = embedding

    def _iterative_retrieve(
        self,
        aspect_name: str,
        query: str,
        aspect_description: str,
        items: List[MemoryItem],
    ) -> List[MemoryItem]:
        if not items:
            return []

        refined_query = query
        for _ in range(self.retrieval_iterations):
            ranked = self._rank_items(refined_query, items)
            top_items = ranked[: self.retrieval_top_k]
            refined = self._refine_query(
                aspect_name, refined_query, aspect_description, top_items
            )
            if refined:
                refined_query = refined
            else:
                break

        return self._select_items_by_type(refined_query, items)

    def _select_items_by_type(
        self, query: str, items: List[MemoryItem]
    ) -> List[MemoryItem]:
        if not items:
            return []

        summary_items = [item for item in items if item.kind == "summary"]
        triple_items = [item for item in items if item.kind == "triple"]
        fact_items = [item for item in items if item.kind == "fact"]
        chunk_items = [item for item in items if item.kind == "chunk"]

        selected: List[MemoryItem] = []

        if summary_items and self.max_summary > 0:
            selected.extend(self._rank_items(query, summary_items)[: self.max_summary])

        if triple_items and self.min_triples > 0:
            selected.extend(self._rank_items(query, triple_items)[: self.min_triples])

        if fact_items and self.min_facts > 0:
            selected.extend(self._rank_items(query, fact_items)[: self.min_facts])

        if chunk_items and self.min_chunks > 0:
            selected.extend(self._rank_items(query, chunk_items)[: self.min_chunks])

        # Fill remaining slots with top-ranked items overall, avoiding duplicates
        if len(selected) < self.retrieval_top_k:
            ranked_all = self._rank_items(query, items)
            seen = {id(item) for item in selected}
            for item in ranked_all:
                if id(item) in seen:
                    continue
                selected.append(item)
                if len(selected) >= self.retrieval_top_k:
                    break

        return selected

    def _refine_query(
        self,
        aspect_name: str,
        query: str,
        aspect_description: str,
        items: List[MemoryItem],
    ) -> str:
        if not self.model_manager or not self.model_id:
            return ""
        snippet_lines = [f"- {item.text}" for item in items[:5]]
        prompt = REFINE_QUERY_PROMPT.format(
            aspect_name=aspect_name,
            aspect_description=aspect_description,
            query=query,
            snippets="\n".join(snippet_lines),
        )
        return self._generate_text(prompt).strip()

    def _rank_items(self, query: str, items: List[MemoryItem]) -> List[MemoryItem]:
        if all(item.embedding is None for item in items):
            return sorted(
                items,
                key=lambda i: self._overlap_score(query, i.text),
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
                items,
                key=lambda i: self._overlap_score(query, i.text),
                reverse=True,
            )

        scored = [
            (item, self._cosine_similarity(query_embedding, item.embedding))
            for item in items
            if item.embedding is not None
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        ranked = [item for item, _ in scored]

        missing = [item for item in items if item.embedding is None]
        if missing:
            missing_sorted = sorted(
                missing,
                key=lambda i: self._overlap_score(query, i.text),
                reverse=True,
            )
            ranked.extend(missing_sorted)

        return ranked

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
        items: List[MemoryItem],
    ) -> str:
        if not items:
            return ""

        grouped: Dict[str, List[str]] = {
            "summary": [],
            "chunk": [],
            "fact": [],
            "triple": [],
        }
        for item in items:
            grouped.setdefault(item.kind, []).append(item.text)

        sections = [f"[STRUCTURAL MEMORY] Aspect: {aspect_name}"]
        if grouped.get("summary"):
            sections.append("\n[SUMMARY]\n" + "\n".join(grouped["summary"][:1]))
        if grouped.get("chunk"):
            sections.append("\n[CHUNKS]\n" + "\n".join(grouped["chunk"]))
        if grouped.get("fact"):
            sections.append("\n[ATOMIC FACTS]\n" + "\n".join(grouped["fact"]))
        if grouped.get("triple"):
            sections.append("\n[KNOWLEDGE TRIPLES]\n" + "\n".join(grouped["triple"]))

        return "\n".join(sections).strip()
