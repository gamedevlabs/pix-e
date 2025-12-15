"""
Mixed Structural Memory Strategy Module.

Implements the Mixed Structural Memory approach from Zeng et al. (2024).

This module provides four memory structures:
- Chunks: Raw text segments (deterministic)
- Knowledge Triples: Structured relationships (deterministic)
- Atomic Facts: Indivisible information units (LLM-based)
- Summaries: Condensed overviews (LLM-based)

Mixed memory = Chunks ∪ Triples ∪ Atomic Facts ∪ Summaries

Also provides:
- Iterative retrieval with query refinement
- Strategy wrapper for unified interface
- Legacy StructuralMemoryContext for backward compatibility
"""

from pxnodes.llm.context.structural_memory.chunks import (
    Chunk,
    extract_chunks,
    extract_chunks_batch,
)
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
from pxnodes.llm.context.structural_memory.summaries import (
    Summary,
    create_fallback_summary,
    extract_summaries_batch,
    extract_summary,
)
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
    # Chunks (Zeng et al. 2024)
    "Chunk",
    "extract_chunks",
    "extract_chunks_batch",
    # Triples (Zeng et al. 2024)
    "KnowledgeTriple",
    "extract_all_triples",
    "compute_derived_triples",
    # Facts (Zeng et al. 2024)
    "AtomicFact",
    "extract_atomic_facts",
    # Summaries (Zeng et al. 2024)
    "Summary",
    "extract_summary",
    "extract_summaries_batch",
    "create_fallback_summary",
    # Retrieval
    "IterativeRetriever",
    "RetrievalResult",
    "RetrievedMemory",
]
