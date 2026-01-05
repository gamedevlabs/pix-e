"""
Hierarchical Graph Strategy Module.

Implements the user's H-MEM adaptation using deterministic graph traversal
instead of vector similarity for context retrieval.

This module provides:
- 4-layer hierarchical context (Domain, Category, Trace, Episode)
- Explicit path enumeration to/from target nodes
- Pool of prior/future nodes with path listings
- Strategy wrapper for unified interface
"""

from pxnodes.llm.context.hierarchical_graph.layers import (
    build_category_layer,
    build_domain_layer,
    build_episode_layer,
    build_trace_layer,
)
from pxnodes.llm.context.hierarchical_graph.strategy import HierarchicalGraphStrategy
from pxnodes.llm.context.hierarchical_graph.traversal import (
    forward_bfs,
    reverse_bfs,
)

__all__ = [
    # Strategy
    "HierarchicalGraphStrategy",
    # Layer Building
    "build_domain_layer",
    "build_category_layer",
    "build_trace_layer",
    "build_episode_layer",
    # Traversal (kept for backwards compatibility)
    "reverse_bfs",
    "forward_bfs",
]
