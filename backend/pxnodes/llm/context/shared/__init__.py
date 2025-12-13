"""
Shared utilities for context engineering strategies.

These modules are used by multiple strategies:
- embeddings: OpenAI embedding generation
- vector_store: SQLite-vec storage and retrieval
- graph_retrieval: Graph topology traversal
- llm_adapter: LLM provider adapter
- prompts: Shared prompt templates for extraction
"""

from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
from pxnodes.llm.context.shared.graph_retrieval import (
    GraphSlice,
    get_all_paths_through_node,
    get_graph_slice,
)
from pxnodes.llm.context.shared.llm_adapter import (
    LLMProviderAdapter,
    create_llm_provider,
)
from pxnodes.llm.context.shared.prompts import (
    ATOMIC_FACT_EXTRACTION_PROMPT,
    KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT,
    MIXED_CONTEXT_TEMPLATE,
    format_components_for_prompt,
    format_fact,
    format_triple,
)
from pxnodes.llm.context.shared.vector_store import VectorStore, init_database

__all__ = [
    # Embeddings
    "OpenAIEmbeddingGenerator",
    # Vector Store
    "VectorStore",
    "init_database",
    # Graph Retrieval
    "GraphSlice",
    "get_graph_slice",
    "get_all_paths_through_node",
    # LLM Adapter
    "LLMProviderAdapter",
    "create_llm_provider",
    # Prompts
    "ATOMIC_FACT_EXTRACTION_PROMPT",
    "KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT",
    "MIXED_CONTEXT_TEMPLATE",
    "format_components_for_prompt",
    "format_triple",
    "format_fact",
]
