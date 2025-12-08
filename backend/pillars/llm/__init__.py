"""
Pillars LLM Operations

This package contains all LLM operation handlers for the pillars feature.
Handlers and agent workflows are auto-registered when this package is imported.
"""

# Import handlers to trigger auto-registration via class definition
from pillars.llm import handlers, workflows  # noqa: F401

__all__ = ["handlers", "workflows"]
