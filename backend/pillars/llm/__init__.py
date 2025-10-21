"""
Pillars LLM Operations

This package contains all LLM operation handlers for the pillars feature.
Handlers are auto-registered when this package is imported.
"""

# Import handlers to trigger auto-registration
from pillars.llm import handlers  # noqa: F401

__all__ = ["handlers"]
