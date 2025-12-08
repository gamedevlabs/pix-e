"""
SPARC LLM orchestration.

This module contains agents, workflows, handlers, and prompts for
SPARC game design evaluation using LLM orchestration.

Handlers and workflows are auto-registered when this package is imported.
"""

# Import handlers and workflows to trigger auto-registration via class definition
from sparc.llm import handlers, workflows  # noqa: F401

__all__ = ["handlers", "workflows"]
