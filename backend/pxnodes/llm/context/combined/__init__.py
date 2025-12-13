"""
Combined Strategy Module.

Combines Structural Memory (Zeng et al. 2024) data representation with
H-MEM (Sun & Zeng 2025) hierarchical organization.

This module provides:
- Knowledge Triples + Atomic Facts for structured data
- 4-layer hierarchical organization for context
- Best of both approaches for thesis comparison
"""

from pxnodes.llm.context.combined.strategy import CombinedStrategy

__all__ = [
    "CombinedStrategy",
]
