"""
Mixed Structural Memory Strategy Module.

Lazy re-exports avoid heavy imports during module load.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "StructuralMemoryStrategy",
    "SimpleStructuralMemoryStrategy",
    "StructuralMemoryContext",
    "StructuralMemoryResult",
    "build_context",
    "get_context_stats",
    "Chunk",
    "extract_chunks",
    "extract_chunks_batch",
    "KnowledgeTriple",
    "extract_llm_triples_only",
    "AtomicFact",
    "extract_atomic_facts",
    "Summary",
    "extract_summary",
    "extract_summaries_batch",
    "create_fallback_summary",
    "IterativeRetriever",
    "RetrievalResult",
    "RetrievedMemory",
]

_EXPORTS: dict[str, tuple[str, str]] = {
    "StructuralMemoryStrategy": (
        "pxnodes.llm.context.structural_memory.strategy",
        "StructuralMemoryStrategy",
    ),
    "SimpleStructuralMemoryStrategy": (
        "pxnodes.llm.context.structural_memory.strategy",
        "SimpleStructuralMemoryStrategy",
    ),
    "StructuralMemoryContext": (
        "pxnodes.llm.context.structural_memory.context",
        "StructuralMemoryContext",
    ),
    "StructuralMemoryResult": (
        "pxnodes.llm.context.structural_memory.context",
        "StructuralMemoryResult",
    ),
    "build_context": ("pxnodes.llm.context.structural_memory.context", "build_context"),
    "get_context_stats": (
        "pxnodes.llm.context.structural_memory.context",
        "get_context_stats",
    ),
    "Chunk": ("pxnodes.llm.context.structural_memory.chunks", "Chunk"),
    "extract_chunks": ("pxnodes.llm.context.structural_memory.chunks", "extract_chunks"),
    "extract_chunks_batch": (
        "pxnodes.llm.context.structural_memory.chunks",
        "extract_chunks_batch",
    ),
    "KnowledgeTriple": (
        "pxnodes.llm.context.structural_memory.triples",
        "KnowledgeTriple",
    ),
    "extract_llm_triples_only": (
        "pxnodes.llm.context.structural_memory.triples",
        "extract_llm_triples_only",
    ),
    "AtomicFact": ("pxnodes.llm.context.structural_memory.facts", "AtomicFact"),
    "extract_atomic_facts": (
        "pxnodes.llm.context.structural_memory.facts",
        "extract_atomic_facts",
    ),
    "Summary": ("pxnodes.llm.context.structural_memory.summaries", "Summary"),
    "extract_summary": (
        "pxnodes.llm.context.structural_memory.summaries",
        "extract_summary",
    ),
    "extract_summaries_batch": (
        "pxnodes.llm.context.structural_memory.summaries",
        "extract_summaries_batch",
    ),
    "create_fallback_summary": (
        "pxnodes.llm.context.structural_memory.summaries",
        "create_fallback_summary",
    ),
    "IterativeRetriever": (
        "pxnodes.llm.context.structural_memory.retriever",
        "IterativeRetriever",
    ),
    "RetrievalResult": (
        "pxnodes.llm.context.structural_memory.retriever",
        "RetrievalResult",
    ),
    "RetrievedMemory": (
        "pxnodes.llm.context.structural_memory.retriever",
        "RetrievedMemory",
    ),
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _EXPORTS[name]
    module = importlib.import_module(module_name)
    return getattr(module, attr_name)


def __dir__() -> list[str]:
    return sorted(list(__all__))
