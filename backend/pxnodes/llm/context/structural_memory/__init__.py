"""
Structural Memory Strategy Module.

Implements the Mixed Structural Memory approach from Zeng et al. (2024).

This module provides:
- Knowledge Triple extraction (deterministic)
- Atomic Fact extraction (LLM-based)
- Iterative retrieval with query refinement
- Strategy wrapper for unified interface
- Legacy StructuralMemoryContext for backward compatibility
"""

from pxnodes.llm.context.structural_memory.context import (
    StructuralMemoryContext,
    StructuralMemoryResult,
    build_context,
    get_context_stats,
)
from pxnodes.llm.context.structural_memory.facts import (
    AtomicFact,
    extract_atomic_facts,
)
from pxnodes.llm.context.structural_memory.retriever import (
    IterativeRetriever,
    RetrievalResult,
    RetrievedMemory,
)
from pxnodes.llm.context.structural_memory.strategy import StructuralMemoryStrategy
from pxnodes.llm.context.structural_memory.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)

__all__ = [
    # Strategy (new)
    "StructuralMemoryStrategy",
    # Context Builder (legacy interface)
    "StructuralMemoryContext",
    "StructuralMemoryResult",
    "build_context",
    "get_context_stats",
    # Triples
    "KnowledgeTriple",
    "extract_all_triples",
    "compute_derived_triples",
    # Facts
    "AtomicFact",
    "extract_atomic_facts",
    # Retrieval
    "IterativeRetriever",
    "RetrievalResult",
    "RetrievedMemory",
]
