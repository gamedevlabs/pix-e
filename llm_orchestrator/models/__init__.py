"""
Model provider abstraction layer.

Includes:
- Provider implementations (Ollama, OpenAI, Gemini)
- Capability matching and filtering utilities
- ModelManager for centralized model operations
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
from llm_orchestrator.models.manager import ModelManager

__all__ = [
    # Model Manager
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

