"""
LLM Provider Package

Standalone package for local LLM provider (Ollama).
This package can be imported by the orchestrator to access local models.
"""

__version__ = "0.1.0"

from llm_provider.base import (BaseProvider, GenerationResult,
                               ModelCapabilities, ModelDetails, ProviderType)
from llm_provider.ollama import (ModelUnavailableError, OllamaProvider,
                                 ProviderError)

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
    # Exceptions (temporarily here until orchestrator provides them)
    "ProviderError",
    "ModelUnavailableError",
]
