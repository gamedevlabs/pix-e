"""
Base provider interface for LLM providers.
All provider implementations (Ollama, OpenAI, Gemini) inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from llm.types import ModelDetails, ProviderType


class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Providers handle communication with specific LLM services
    (Ollama, OpenAI, Gemini, etc.) and abstract away their differences.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.

        Args:
            config: Provider-specific configuration (API keys, URLs, etc.)
        """
        self.config = config
        self._is_available: Optional[bool] = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get provider name (e.g., 'ollama', 'openai', 'gemini')."""
        pass

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get provider type ('local' or 'cloud')."""
        pass

    @abstractmethod
    def list_models(self) -> List[ModelDetails]:
        """
        List all available models from this provider.

        Returns:
            List of ModelDetails with capabilities
        """
        pass

    @abstractmethod
    def generate_text(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using the specified model.

        Args:
            model_name: Name of the model to use
            prompt: Text prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
        """
        pass

    @abstractmethod
    def generate_structured(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured output (JSON) using the specified model.

        Args:
            model_name: Name of the model to use
            prompt: Text prompt
            response_schema: Pydantic model for response structure
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and reachable.
        """
        pass

    @abstractmethod
    def get_model_info(self, model_name: str) -> ModelDetails:
        """
        Get detailed information about a specific model.
        """
        pass

    def supports_capability(self, model_name: str, capability: str) -> bool:
        """
        Check if a model supports a specific capability.

        Args:
            model_name: Name of the model
            capability: Capability to check (e.g., 'json_strict', 'vision')
        """
        try:
            model_info = self.get_model_info(model_name)
            return getattr(model_info.capabilities, capability, False) or False
        except Exception:
            return False

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_name}, type={self.provider_type})"  # noqa: E501


class GenerationResult:
    """Result from text generation."""

    def __init__(
        self,
        text: str,
        model: str,
        provider: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.model = model
        self.provider = provider
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.metadata = metadata or {}


class StructuredResult:
    """Result from structured generation with token tracking."""

    def __init__(
        self,
        data: Any,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        model: str = "",
        provider: str = "",
    ):
        self.data = data
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.model = model
        self.provider = provider

    def model_dump(self) -> Dict[str, Any]:
        """Pass through to underlying data's model_dump if available."""
        if hasattr(self.data, "model_dump"):
            return self.data.model_dump()
        return self.data
