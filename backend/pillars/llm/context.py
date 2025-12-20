"""
Context builder for Pillars evaluation strategies.
"""

import asyncio
import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from game_concept.models import GameConcept
from llm.config import get_config
from llm.logfire_config import get_logfire
from llm.providers.manager import ModelManager
from pillars.models import Pillar
from pillars.utils import format_pillars_text
from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator

logger = logging.getLogger(__name__)


class PillarsContextStrategy(Enum):
    """Available context strategies for Pillars."""

    RAW = "raw"
    STRUCTURAL_MEMORY = "structural_memory"
    HMEM = "hmem"
    COMBINED = "combined"


@dataclass
class PillarsContextResult:
    """Resolved context payload for Pillars handlers."""

    pillars_text: str
    context_text: str
    strategy: PillarsContextStrategy
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class MemoryItem:
    """Memory unit for Pillars retrieval."""

    kind: str
    text: str
    embedding: Optional[List[float]] = None


ATOMICS_CONCEPT_PROMPT = """Extract atomic facts from the game concept.

Rules:
- Each fact must be a short sentence.
- No numbering or bullet symbols.
- Do not invent information.

Game concept:
{game_text}

Atomic facts:"""

TRIPLES_CONCEPT_PROMPT = """Extract knowledge triples from the game concept.

Rules:
- Format each triple as: (Head, Relation, Tail)
- One triple per line.
- Do not invent information.

Game concept:
{game_text}

Triples:"""

SUMMARY_CONCEPT_PROMPT = """Provide a concise summary of the game concept.

Rules:
- 3 to 5 sentences.
- Capture core gameplay, goals, setting, and unique features.
- Do not invent information.

Game concept:
{game_text}

Summary:"""

ATOMICS_PILLARS_PROMPT = """Extract atomic facts from the design pillars.

Rules:
- Each fact must be a short sentence.
- No numbering or bullet symbols.
- Include pillar names when relevant.
- Do not invent information.

Pillars:
{pillars_text}

Atomic facts:"""

TRIPLES_PILLARS_PROMPT = """Extract knowledge triples from the design pillars.

Rules:
- Format each triple as: (Head, Relation, Tail)
- One triple per line.
- Use pillar names as entities where possible.
- Do not invent information.

Pillars:
{pillars_text}

Triples:"""

SUMMARY_PILLARS_PROMPT = """Provide concise summaries for each pillar.

Rules:
- Output one line per pillar in the format: [ID: X] Summary: ...
- 1 sentence per pillar.
- Do not invent information.

Pillars:
{pillars_text}

Summaries:"""

REFINE_QUERY_PROMPT = """Refine the retrieval query for a pillars evaluation task.

Task: {operation}
Current query: {query}

Relevant memory snippets:
{snippets}

Return a single, more specific query line that will retrieve the most relevant
information for this task. Do not include extra text."""


OPERATION_QUERIES = {
    "evaluate_completeness": (
        "Find missing design coverage, gaps in pillars, unaddressed mechanics, "
        "themes, tone, audience, progression, or constraints."
    ),
    "evaluate_contradictions": (
        "Find conflicts or contradictions between pillars or between pillars "
        "and the game concept."
    ),
    "suggest_additions": (
        "Identify missing pillars, goals, or design values needed to cover the concept."
    ),
    "evaluate_context": ("Assess alignment between the game concept and the pillars."),
    "resolve_contradictions": (
        "Focus on conflicting pillar requirements and how they can be reconciled."
    ),
    "evaluate_all": (
        "Assess coverage, contradictions, missing pillars, and alignment overall."
    ),
}


def build_pillars_context(
    pillars: List[Pillar],
    game_concept: GameConcept,
    strategy_name: Optional[str] = None,
    model_id: Optional[str] = None,
    operation: Optional[str] = None,
) -> PillarsContextResult:
    """
    Build context payload for pillars handlers.

    This is the shared entry point for swapping strategies from the API layer.
    """
    try:
        strategy = (
            PillarsContextStrategy(strategy_name)
            if strategy_name
            else PillarsContextStrategy.RAW
        )
    except ValueError:
        strategy = PillarsContextStrategy.RAW

    pillars_text = format_pillars_text(pillars)
    context_text = game_concept.content

    if strategy == PillarsContextStrategy.RAW:
        return PillarsContextResult(
            pillars_text=pillars_text,
            context_text=context_text,
            strategy=strategy,
        )

    logfire = get_logfire()
    op_name = operation or "evaluate_all"

    model_manager = _resolve_model_manager(model_id)

    with logfire.span(
        "pillars.context_strategy.build",
        strategy=strategy.value,
        operation=op_name,
        pillars_count=len(pillars),
    ):
        if strategy == PillarsContextStrategy.STRUCTURAL_MEMORY:
            return _build_structural_memory_context(
                pillars_text,
                context_text,
                strategy,
                model_manager,
                model_id,
                operation,
            )

        if strategy == PillarsContextStrategy.HMEM:
            return _build_hmem_context(
                pillars_text,
                context_text,
                strategy,
                model_manager,
                model_id,
                operation,
            )

        if strategy == PillarsContextStrategy.COMBINED:
            return _build_combined_context(
                pillars_text,
                context_text,
                strategy,
                model_manager,
                model_id,
                operation,
            )

    return PillarsContextResult(
        pillars_text=pillars_text,
        context_text=context_text,
        strategy=PillarsContextStrategy.RAW,
        metadata={"strategy_warning": "unknown strategy fallback"},
    )


def _resolve_model_manager(model_id: Optional[str]) -> Optional[ModelManager]:
    if not model_id:
        return None
    try:
        return ModelManager(get_config())
    except Exception as exc:
        logger.warning("Failed to initialize model manager: %s", exc)
        return None


def _build_structural_memory_context(
    pillars_text: str,
    context_text: str,
    strategy: PillarsContextStrategy,
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    operation: Optional[str],
) -> PillarsContextResult:
    concept_chunks = _chunk_text(context_text)
    (
        concept_summary,
        concept_facts,
        concept_triples,
        pillar_facts,
        pillar_triples,
        _pillar_summaries,
    ) = _run_parallel_extractions(
        model_manager,
        model_id,
        context_text,
        pillars_text,
        need_summary=True,
        need_triples=True,
        need_pillar_summaries=False,
    )

    op_name = operation or "evaluate_all"
    query = _build_operation_query(op_name)

    concept_items = _build_memory_items(
        concept_summary, concept_chunks, concept_facts, concept_triples, "concept"
    )
    pillar_items = _build_memory_items("", [], pillar_facts, pillar_triples, "pillars")

    _attach_embeddings(concept_items, model_manager, model_id)
    _attach_embeddings(pillar_items, model_manager, model_id)

    concept_selected = _iterative_retrieve(
        model_manager, model_id, query, concept_items, operation=op_name
    )
    pillar_selected = _iterative_retrieve(
        model_manager, model_id, query, pillar_items, operation=op_name
    )

    structured_context = _assemble_structural_context_from_items(
        concept_selected, label="GAME CONCEPT"
    )
    structured_pillars = _assemble_structural_context_from_items(
        pillar_selected, label="PILLARS"
    )

    return PillarsContextResult(
        pillars_text=structured_pillars,
        context_text=structured_context,
        strategy=strategy,
        metadata={"strategy": strategy.value},
    )


def _build_hmem_context(
    pillars_text: str,
    context_text: str,
    strategy: PillarsContextStrategy,
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    operation: Optional[str],
) -> PillarsContextResult:
    concept_chunks = _chunk_text(context_text)
    (
        concept_summary,
        _concept_facts,
        _concept_triples,
        _pillar_facts,
        _pillar_triples,
        pillar_summaries,
    ) = _run_parallel_extractions(
        model_manager,
        model_id,
        context_text,
        pillars_text,
        need_summary=True,
        need_triples=False,
        need_pillar_summaries=True,
    )
    pillar_lines = [line for line in pillars_text.split("\n") if line.strip()]

    op_name = operation or "evaluate_all"
    query = _build_operation_query(op_name)
    trace_items = [MemoryItem(kind="trace", text=chunk) for chunk in concept_chunks]
    episode_items = [MemoryItem(kind="episode", text=line) for line in pillar_lines]

    _attach_embeddings(trace_items, model_manager, model_id)
    _attach_embeddings(episode_items, model_manager, model_id)

    selected_traces = _select_top_items(query, trace_items, 6)
    selected_episodes = _select_top_items(query, episode_items, 6)

    hmem_context = _assemble_hmem_context(
        concept_summary,
        pillar_summaries,
        [item.text for item in selected_traces],
        [item.text for item in selected_episodes],
    )
    return PillarsContextResult(
        pillars_text=pillars_text,
        context_text=hmem_context,
        strategy=strategy,
        metadata={"strategy": strategy.value},
    )


def _build_combined_context(
    pillars_text: str,
    context_text: str,
    strategy: PillarsContextStrategy,
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    operation: Optional[str],
) -> PillarsContextResult:
    concept_chunks = _chunk_text(context_text)
    (
        concept_summary,
        concept_facts,
        concept_triples,
        pillar_facts,
        pillar_triples,
        pillar_summaries,
    ) = _run_parallel_extractions(
        model_manager,
        model_id,
        context_text,
        pillars_text,
        need_summary=True,
        need_triples=True,
        need_pillar_summaries=True,
    )

    op_name = operation or "evaluate_all"
    query = _build_operation_query(op_name)
    trace_items = [MemoryItem(kind="trace", text=chunk) for chunk in concept_chunks]
    memory_items = _build_memory_items(
        concept_summary,
        [],
        concept_facts + pillar_facts,
        concept_triples + pillar_triples,
        "combined",
    )

    _attach_embeddings(trace_items, model_manager, model_id)
    _attach_embeddings(memory_items, model_manager, model_id)

    selected_traces = _select_top_items(query, trace_items, 6)
    selected_items = _iterative_retrieve(
        model_manager, model_id, query, memory_items, operation=op_name
    )

    combined_context = _assemble_combined_context(
        concept_summary,
        pillar_summaries,
        [item.text for item in selected_traces],
        _collect_texts(selected_items, "fact"),
        _collect_texts(selected_items, "triple"),
    )
    return PillarsContextResult(
        pillars_text=pillars_text,
        context_text=combined_context,
        strategy=strategy,
        metadata={"strategy": strategy.value},
    )


def _generate_text(
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    prompt: str,
) -> str:
    if not model_manager or not model_id:
        return ""

    try:
        result = model_manager.generate_with_model(
            model_id, prompt, temperature=0.2, max_tokens=800
        )
        return result.text.strip()
    except Exception as exc:
        logger.warning("Pillars context generation failed: %s", exc)
        return ""


def _build_operation_query(operation: Optional[str]) -> str:
    if not operation:
        return OPERATION_QUERIES["evaluate_all"]
    return OPERATION_QUERIES.get(operation, OPERATION_QUERIES["evaluate_all"])


def _build_memory_items(
    summary: str,
    chunks: list[str],
    facts: list[str],
    triples: list[str],
    prefix: str,
) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    if summary:
        items.append(MemoryItem(kind=f"{prefix}_summary", text=summary))
    items.extend(MemoryItem(kind=f"{prefix}_chunk", text=chunk) for chunk in chunks)
    items.extend(MemoryItem(kind=f"{prefix}_fact", text=fact) for fact in facts)
    items.extend(MemoryItem(kind=f"{prefix}_triple", text=triple) for triple in triples)
    return items


def _attach_embeddings(
    items: list[MemoryItem],
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
) -> None:
    if not items or not model_manager or not model_id:
        return
    try:
        embedder = OpenAIEmbeddingGenerator()
        embeddings = embedder.generate_embeddings_batch([item.text for item in items])
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return

    for item, embedding in zip(items, embeddings):
        item.embedding = embedding


def _rank_items(query: str, items: list[MemoryItem]) -> list[MemoryItem]:
    if not items:
        return []

    if all(item.embedding is None for item in items):
        return sorted(items, key=lambda i: _overlap_score(query, i.text), reverse=True)

    query_embedding = None
    try:
        embedder = OpenAIEmbeddingGenerator()
        query_embedding = embedder.generate_embedding(query)
    except Exception as exc:
        logger.warning("Query embedding failed: %s", exc)

    if query_embedding is None:
        return sorted(items, key=lambda i: _overlap_score(query, i.text), reverse=True)

    scored = [
        (item, _cosine_similarity(query_embedding, item.embedding))
        for item in items
        if item.embedding is not None
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    ranked = [item for item, _ in scored]

    missing = [item for item in items if item.embedding is None]
    if missing:
        missing_sorted = sorted(
            missing, key=lambda i: _overlap_score(query, i.text), reverse=True
        )
        ranked.extend(missing_sorted)

    return ranked


def _iterative_retrieve(
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    query: str,
    items: list[MemoryItem],
    *,
    operation: str,
    iterations: int = 2,
    top_k: int = 10,
) -> list[MemoryItem]:
    if not items:
        return []

    refined_query = query
    for _ in range(iterations):
        ranked = _rank_items(refined_query, items)
        top_items = ranked[:top_k]
        refined = _refine_query(
            model_manager, model_id, refined_query, top_items, operation
        )
        if refined:
            refined_query = refined
        else:
            break

    ranked = _rank_items(refined_query, items)
    return _select_items_by_type(ranked, top_k=top_k)


def _select_top_items(
    query: str, items: list[MemoryItem], top_k: int
) -> list[MemoryItem]:
    return _rank_items(query, items)[:top_k]


def _select_items_by_type(
    ranked: list[MemoryItem],
    *,
    top_k: int,
    min_triples: int = 3,
    min_facts: int = 8,
    min_chunks: int = 3,
    max_summary: int = 1,
) -> list[MemoryItem]:
    if not ranked:
        return []

    summary_items = [item for item in ranked if "summary" in item.kind]
    triple_items = [item for item in ranked if "triple" in item.kind]
    fact_items = [item for item in ranked if "fact" in item.kind]
    chunk_items = [item for item in ranked if "chunk" in item.kind]

    selected: list[MemoryItem] = []
    if summary_items and max_summary > 0:
        selected.extend(summary_items[:max_summary])
    if triple_items and min_triples > 0:
        selected.extend(triple_items[:min_triples])
    if fact_items and min_facts > 0:
        selected.extend(fact_items[:min_facts])
    if chunk_items and min_chunks > 0:
        selected.extend(chunk_items[:min_chunks])

    if len(selected) < top_k:
        seen = {id(item) for item in selected}
        for item in ranked:
            if id(item) in seen:
                continue
            selected.append(item)
            if len(selected) >= top_k:
                break

    return selected


def _refine_query(
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    query: str,
    items: list[MemoryItem],
    operation: str,
) -> str:
    if not model_manager or not model_id:
        return ""
    snippet_lines = [f"- {item.text}" for item in items[:5]]
    prompt = REFINE_QUERY_PROMPT.format(
        operation=operation,
        query=query,
        snippets="\n".join(snippet_lines),
    )
    return _generate_text(model_manager, model_id, prompt).strip()


def _overlap_score(query: str, text: str) -> int:
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text_tokens = set(re.findall(r"\w+", text.lower()))
    return len(query_tokens.intersection(text_tokens))


def _cosine_similarity(
    vec_a: Optional[list[float]], vec_b: Optional[list[float]]
) -> float:
    if vec_a is None or vec_b is None:
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _collect_texts(items: list[MemoryItem], kind_contains: str) -> list[str]:
    return [item.text for item in items if kind_contains in item.kind]


def _run_parallel_extractions(
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    context_text: str,
    pillars_text: str,
    *,
    need_summary: bool,
    need_triples: bool,
    need_pillar_summaries: bool = False,
) -> tuple[str, list[str], list[str], list[str], list[str], list[str]]:
    if not model_manager or not model_id:
        return "", [], [], [], [], []

    async def run() -> (
        tuple[str, list[str], list[str], list[str], list[str], list[str]]
    ):
        tasks = []

        summary_task = None
        if need_summary:
            summary_task = asyncio.to_thread(
                _generate_text,
                model_manager,
                model_id,
                SUMMARY_CONCEPT_PROMPT.format(game_text=context_text),
            )
            tasks.append(summary_task)

        concept_facts_task = asyncio.to_thread(
            _generate_text,
            model_manager,
            model_id,
            ATOMICS_CONCEPT_PROMPT.format(game_text=context_text),
        )
        tasks.append(concept_facts_task)

        concept_triples_task = None
        if need_triples:
            concept_triples_task = asyncio.to_thread(
                _generate_text,
                model_manager,
                model_id,
                TRIPLES_CONCEPT_PROMPT.format(game_text=context_text),
            )
            tasks.append(concept_triples_task)

        pillar_facts_task = asyncio.to_thread(
            _generate_text,
            model_manager,
            model_id,
            ATOMICS_PILLARS_PROMPT.format(pillars_text=pillars_text),
        )
        tasks.append(pillar_facts_task)

        pillar_triples_task = None
        if need_triples:
            pillar_triples_task = asyncio.to_thread(
                _generate_text,
                model_manager,
                model_id,
                TRIPLES_PILLARS_PROMPT.format(pillars_text=pillars_text),
            )
            tasks.append(pillar_triples_task)

        pillar_summaries_task = None
        if need_pillar_summaries:
            pillar_summaries_task = asyncio.to_thread(
                _generate_text,
                model_manager,
                model_id,
                SUMMARY_PILLARS_PROMPT.format(pillars_text=pillars_text),
            )
            tasks.append(pillar_summaries_task)

        results = await asyncio.gather(*tasks)
        idx = 0

        summary_text = ""
        if summary_task:
            summary_text = results[idx] if idx < len(results) else ""
            idx += 1

        concept_facts = _split_lines(results[idx] if idx < len(results) else "")
        idx += 1

        concept_triples = []
        if concept_triples_task:
            concept_triples = _split_lines(results[idx] if idx < len(results) else "")
            idx += 1

        pillar_facts = _split_lines(results[idx] if idx < len(results) else "")
        idx += 1

        pillar_triples = []
        if pillar_triples_task:
            pillar_triples = _split_lines(results[idx] if idx < len(results) else "")
            idx += 1

        pillar_summaries = []
        if pillar_summaries_task:
            pillar_summaries = _split_lines(results[idx] if idx < len(results) else "")

        return (
            summary_text,
            concept_facts,
            concept_triples,
            pillar_facts,
            pillar_triples,
            pillar_summaries,
        )

    return asyncio.run(run())


def _split_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if not cleaned:
            continue
        lines.append(cleaned)
    return lines


def _chunk_text(text: str, max_chunk_chars: int = 800) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chunk_chars:
            chunks.append(paragraph)
            continue
        current: list[str] = []
        current_len = 0
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            if not sentence:
                continue
            if current_len + len(sentence) > max_chunk_chars and current:
                chunks.append(" ".join(current))
                current = []
                current_len = 0
            current.append(sentence)
            current_len += len(sentence) + 1
        if current:
            chunks.append(" ".join(current))
    return chunks


def _assemble_structural_context(
    summary: str,
    chunks: list[str],
    facts: list[str],
    triples: list[str],
) -> str:
    sections = ["[STRUCTURAL MEMORY: GAME CONCEPT]"]
    if summary:
        sections.append("\n[SUMMARY]\n" + summary)
    if chunks:
        sections.append("\n[CHUNKS]\n" + "\n".join(chunks))
    if facts:
        sections.append("\n[ATOMIC FACTS]\n" + "\n".join(facts))
    if triples:
        sections.append("\n[KNOWLEDGE TRIPLES]\n" + "\n".join(triples))
    return "\n".join(sections).strip()


def _assemble_structural_context_from_items(
    items: list[MemoryItem],
    *,
    label: str,
) -> str:
    sections = [f"[STRUCTURAL MEMORY: {label}]"]
    summaries = _collect_texts(items, "summary")
    chunks = _collect_texts(items, "chunk")
    facts = _collect_texts(items, "fact")
    triples = _collect_texts(items, "triple")

    if summaries:
        sections.append("\n[SUMMARY]\n" + "\n".join(summaries[:1]))
    if chunks:
        sections.append("\n[CHUNKS]\n" + "\n".join(chunks))
    if facts:
        sections.append("\n[ATOMIC FACTS]\n" + "\n".join(facts))
    if triples:
        sections.append("\n[KNOWLEDGE TRIPLES]\n" + "\n".join(triples))
    return "\n".join(sections).strip()


def _assemble_structural_pillars(
    pillars_text: str,
    facts: list[str],
    triples: list[str],
) -> str:
    sections = ["[STRUCTURAL MEMORY: PILLARS]"]
    if pillars_text:
        sections.append("\n[PILLARS RAW]\n" + pillars_text)
    if facts:
        sections.append("\n[PILLAR ATOMIC FACTS]\n" + "\n".join(facts))
    if triples:
        sections.append("\n[PILLAR TRIPLES]\n" + "\n".join(triples))
    return "\n".join(sections).strip()


def _assemble_hmem_context(
    domain_summary: str,
    pillar_summaries: list[str],
    traces: list[str],
    episodes: list[str],
) -> str:
    sections = ["[H-MEM: PILLARS]"]
    if domain_summary:
        sections.append("\n[L1 DOMAIN]\n" + domain_summary)
    if pillar_summaries:
        sections.append("\n[L2 CATEGORY]\n" + "\n".join(pillar_summaries))
    if traces:
        sections.append("\n[L3 TRACE]\n" + "\n".join(traces))
    if episodes:
        sections.append("\n[L4 EPISODES]\n" + "\n".join(episodes))
    return "\n".join(sections).strip()


def _assemble_combined_context(
    domain_summary: str,
    pillar_summaries: list[str],
    traces: list[str],
    facts: list[str],
    triples: list[str],
) -> str:
    sections = ["[COMBINED: PILLARS]"]
    if domain_summary:
        sections.append("\n[L1 DOMAIN]\n" + domain_summary)
    if pillar_summaries:
        sections.append("\n[L2 CATEGORY]\n" + "\n".join(pillar_summaries))
    if traces:
        sections.append("\n[L3 TRACE]\n" + "\n".join(traces))
    if facts:
        sections.append("\n[L4 ATOMIC FACTS]\n" + "\n".join(facts))
    if triples:
        sections.append("\n[L4 KNOWLEDGE TRIPLES]\n" + "\n".join(triples))
    return "\n".join(sections).strip()
