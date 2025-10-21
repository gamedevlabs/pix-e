"""
Local LLM providers (project root package).

This package contains local provider implementations like Ollama.
"""

__version__ = "0.1.0"

from local_llm.base import (
    BaseProvider,
    GenerationResult,
    ModelCapabilities,
    ModelDetails,
    ProviderType,
)
from local_llm.ollama import ModelUnavailableError, OllamaProvider, ProviderError

__all__ = [
    # Base classes
    "BaseProvider",
    "GenerationResult",
    # Types
    "ProviderType",
    "ModelCapabilities",
    "ModelDetails",
    # Ollama provider
    "OllamaProvider",
    # Exceptions
    "ProviderError",
    "ModelUnavailableError",
]


