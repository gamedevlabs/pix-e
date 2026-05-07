"""
H-MEM Strategy Module.

Implements the true H-MEM approach from Sun & Zeng (2025)
"H-MEM: Hierarchical Memory for High-Efficiency Long-Term Reasoning".

This module provides:
- Vector embeddings with positional index routing
- 4-layer hierarchical memory (Domain, Category, Trace, Episode)
- Django model storage for persistent embeddings
- Semantic similarity retrieval

Key differences from HierarchicalGraphStrategy:
- Uses vector similarity instead of graph traversal
- Embeddings stored in Django database
- Positional index encoding for hierarchical routing
"""

from pxnodes.llm.context.hmem.retriever import (
    HMEMContextResult,
    HMEMRetrievalResult,
    HMEMRetriever,
    compute_path_hash,
)
from pxnodes.llm.context.hmem.strategy import HMEMStrategy

__all__ = [
    # Strategy
    "HMEMStrategy",
    # Retriever
    "HMEMRetriever",
    "HMEMRetrievalResult",
    "HMEMContextResult",
    # Utilities
    "compute_path_hash",
]
