"""
LLM Provider implementations for the orchestrator.

This package contains all provider implementations:
- Local providers: Ollama
- Cloud providers: OpenAI, Gemini
"""

# Lightweight imports only — heavy SDKs (openai, google.genai) are imported
# internally by each provider when first used, not at package import time.
# This avoids loading 100MB+ of SDK dependencies when the LLM module is
# imported (e.g. during test database setup), which caused OOM crashes.
from llm.providers.base import BaseProvider, GenerationResult
from llm.providers.capabilities import (
    compare_capabilities,
    filter_by_capabilities,
    find_best_model,
    get_capability_summary,
    get_models_with_capability,
    matches_requirements,
    rank_models,
)
from llm.providers.manager import ModelManager
from llm.providers.ollama_provider import OllamaProvider

__all__ = [
    "BaseProvider",
    "GenerationResult",
    "OllamaProvider",
    "ModelManager",
    "compare_capabilities",
    "filter_by_capabilities",
    "find_best_model",
    "get_capability_summary",
    "get_models_with_capability",
    "matches_requirements",
    "rank_models",
]
