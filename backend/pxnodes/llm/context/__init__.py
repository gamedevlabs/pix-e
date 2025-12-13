"""
Structural Memory Context Strategy.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
for converting PX Nodes/Charts into Knowledge Triples and Atomic Facts.
"""

from pxnodes.llm.context.change_detection import (
    compute_node_content_hash,
    get_changed_nodes,
    get_processing_stats,
    has_node_changed,
    update_processing_state,
)
from pxnodes.llm.context.embeddings import (
    OpenAIEmbeddingGenerator,
    generate_embedding,
)
from pxnodes.llm.context.generator import (
    GenerationResult,
    StructuralMemoryGenerator,
    generate_structural_memory,
)
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter, create_llm_provider
from pxnodes.llm.context.structural_memory import StructuralMemoryContext
from pxnodes.llm.context.vector_store import VectorStore

__all__ = [
    # Core
    "StructuralMemoryContext",
    "VectorStore",
    # Generation
    "StructuralMemoryGenerator",
    "GenerationResult",
    "generate_structural_memory",
    # Change Detection
    "compute_node_content_hash",
    "has_node_changed",
    "get_changed_nodes",
    "get_processing_stats",
    "update_processing_state",
    # Embeddings
    "OpenAIEmbeddingGenerator",
    "generate_embedding",
    # LLM
    "LLMProviderAdapter",
    "create_llm_provider",
]
