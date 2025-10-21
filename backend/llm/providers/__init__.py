"""
LLM Provider implementations for the orchestrator.

This package contains cloud provider implementations (OpenAI, Gemini).
Local provider (Ollama) is in the standalone llm_provider package.
"""

from llm.providers.capabilities import (
    compare_capabilities,
    filter_by_capabilities,
    find_best_model,
    get_capability_summary,
    get_models_with_capability,
    matches_requirements,
    rank_models,
)
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.manager import ModelManager
from llm.providers.openai_provider import OpenAIProvider

__all__ = [
    # Providers
    "OpenAIProvider",
    "GeminiProvider",
    "ModelManager",
    # Capability utilities
    "matches_requirements",
    "filter_by_capabilities",
    "find_best_model",
    "rank_models",
    "get_capability_summary",
    "get_models_with_capability",
    "compare_capabilities",
]
