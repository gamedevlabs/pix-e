"""
Context management utilities for pix:e.

This module provides context retrieval, formatting, and coherence checking
utilities used across features for context engineering.
"""

from .schemas import CoherenceReport, PillarData, SPARCData, UserContext
from .utils import check_coherence, format_context_for_prompt, get_user_context

__all__ = [
    "get_user_context",
    "format_context_for_prompt",
    "check_coherence",
    "UserContext",
    "PillarData",
    "SPARCData",
    "CoherenceReport",
]
