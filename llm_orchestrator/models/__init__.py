"""
Model provider abstraction layer.

Includes:
- Provider implementations (Ollama, OpenAI, Gemini)
- Capability matching and filtering utilities
"""

from llm_orchestrator.models.capabilities import (
    matches_requirements,
    filter_by_capabilities,
    find_best_model,
    rank_models,
    get_capability_summary,
    get_models_with_capability,
    compare_capabilities,
)

__all__ = [
    # Capability utilities
    "matches_requirements",
    "filter_by_capabilities",
    "find_best_model",
    "rank_models",
    "get_capability_summary",
    "get_models_with_capability",
    "compare_capabilities",
]

