"""
SPARC LLM orchestration.

This module contains agents, graphs, handlers, and prompts for
SPARC game design evaluation using LLM orchestration.

Handlers and graphs are auto-registered when this package is imported.
"""

# Import handlers and graphs to trigger auto-registration via class definition
from sparc.llm import graphs, handlers  # noqa: F401

__all__ = ["handlers", "graphs"]
