"""
Model Manager for the LLM Orchestrator.

Central manager that handles:
- Provider initialization and lifecycle
- Model aggregation from all providers
- Direct model selection (user-specified)
- Automatic model selection (based on requirements)
- Fallback and retry logic
"""

import logging
import time
from typing import Any, Dict, List, Optional

from llm.config import Config, get_config
from llm.exceptions import (
    ModelUnavailableError,
    ProviderError,
)
from llm.providers.base import BaseProvider, GenerationResult
from llm.providers.capabilities import (
    filter_by_capabilities,
    find_best_model,
)
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.ollama_provider import OllamaProvider
from llm.providers.openai_provider import OpenAIProvider
from llm.types import (
    CapabilityRequirements,
    ModelDetails,
    ModelInventory,
    ModelPreference,
)

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Central manager for all LLM providers and models.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the model manager.

        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or get_config()
        self.providers: Dict[str, BaseProvider] = {}
        self._model_cache: Optional[List[ModelDetails]] = None
        self._cache_timestamp: Optional[float] = None

        # Initialize all available providers
        self._init_providers()

    def _init_providers(self) -> None:
        """
        Initialize all configured LLM providers.

        Tries to initialize Ollama, OpenAI, and Gemini based on configuration.
        Providers that fail to initialize are skipped with a warning.
        """
        # Initialize Ollama (local)
        try:
            ollama = OllamaProvider(
                {
                    "base_url": self.config.ollama_base_url,
                    "timeout": self.config.ollama_timeout_seconds,
                }
            )
            if ollama.is_available():
                self.providers["ollama"] = ollama
                logger.info("✅ Ollama provider initialized")
            else:
                logger.info("⚠️  Ollama provider not available")
        except Exception as e:
            logger.warning(f"⚠️  Ollama provider initialization failed: {e}")

        # Initialize OpenAI (cloud)
        if self.config.openai_api_key:
            try:
                openai = OpenAIProvider(
                    {
                        "api_key": self.config.openai_api_key,
                        "organization": self.config.openai_organization,
                        "timeout": self.config.openai_timeout_seconds,
                    }
                )
                if openai.is_available():
                    self.providers["openai"] = openai
                    logger.info("✅ OpenAI provider initialized")
                else:
                    logger.warning("⚠️  OpenAI provider not available")
            except Exception as e:
                logger.warning(f"⚠️  OpenAI provider initialization failed: {e}")
        else:
            logger.info("⚠️  OpenAI API key not configured")

        # Initialize Gemini (cloud)
        if self.config.gemini_api_key:
            try:
                gemini = GeminiProvider(
                    {
                        "api_key": self.config.gemini_api_key,
                        "timeout": self.config.gemini_timeout_seconds,
                    }
                )
                if gemini.is_available():
                    self.providers["gemini"] = gemini
                    logger.info("✅ Gemini provider initialized")
                else:
                    logger.warning("⚠️  Gemini provider not available")
            except Exception as e:
                logger.warning(f"⚠️  Gemini provider initialization failed: {e}")
        else:
            logger.info("⚠️  Gemini API key not configured")

        # Ensure at least one provider is available
        if not self.providers:
            raise ProviderError(
                message="No LLM providers available. Configure at least one provider (Ollama, OpenAI, or Gemini).",  # noqa: E501
                provider="none",
            )

        provider_names = ", ".join(self.providers.keys())
        logger.info(
            f"📊 Initialized {len(self.providers)} provider(s): " f"{provider_names}"
        )

    def list_models(self, refresh: bool = False) -> List[ModelDetails]:
        """
        List all available models from all providers.

        Results are cached for performance. Use refresh=True to bypass cache.
        """
        now = time.time()

        # Check if cache is valid
        if (
            not refresh
            and self._model_cache is not None
            and self._cache_timestamp is not None
            and self.config.cache_enabled
            and now - self._cache_timestamp < self.config.cache_ttl_seconds
        ):
            return self._model_cache

        # Fetch models from all providers
        all_models = []
        for provider_name, provider in self.providers.items():
            try:
                models = provider.list_models()
                all_models.extend(models)
                logger.debug(f"Listed {len(models)} models from {provider_name}")
            except Exception as e:
                logger.warning(f"Failed to list models from {provider_name}: {e}")

        # Update cache
        if self.config.cache_enabled:
            self._model_cache = all_models
            self._cache_timestamp = now

        return all_models

    def list_available_models(
        self,
        provider_filter: Optional[str] = None,
        capability_filter: Optional[CapabilityRequirements] = None,
        refresh: bool = False,
    ) -> List[ModelDetails]:
        """
        List models for frontend selection with optional filtering.
        """
        models = self.list_models(refresh=refresh)

        # Filter by provider
        if provider_filter:
            models = [m for m in models if m.provider == provider_filter]

        # Filter by capabilities
        if capability_filter:
            models = filter_by_capabilities(models, capability_filter)

        return models

    def get_model_inventory(self, refresh: bool = False) -> ModelInventory:
        """
        Get complete model inventory matching API spec.
        """
        models = self.list_models(refresh=refresh)
        return ModelInventory(models=models)

    def _find_model_by_name(self, model_name: str) -> ModelDetails:
        """
        Find a model by name across all providers.
        """
        all_models = self.list_models()

        for model in all_models:
            if model.name == model_name:
                return model

        # Model not found
        available_names = [m.name for m in all_models[:5]]
        available_str = ", ".join(available_names)
        raise ModelUnavailableError(
            model=model_name,
            provider="unknown",
            reason=f"Model not found. Available models: {available_str}...",
        )

    def generate_with_model(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate text using a specific model (user-selected).

        This is the PRIMARY method for user-driven model selection.
        Uses exactly the model specified - no automatic selection.

        Args:
            model_name: Exact model name to use
            prompt: Text prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
        """
        # Find the model
        model = self._find_model_by_name(model_name)
        provider = self.providers[model.provider]

        # Generate with the specified model
        text = provider.generate_text(
            model_name=model.name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return GenerationResult(
            text=text, model=model.name, provider=provider.provider_name
        )

    def generate_structured_with_model(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured output using a specific model (user-selected).

        Args:
            model_name: Exact model name to use
            prompt: Text prompt
            response_schema: Pydantic model for response structure
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
        """
        # Find the model
        model = self._find_model_by_name(model_name)
        provider = self.providers[model.provider]

        # Check if model supports structured output
        if not model.capabilities.json_strict:
            logger.warning(f"Model {model_name} may not have strict JSON support")

        # Generate structured output
        return provider.generate_structured(
            model_name=model.name,
            prompt=prompt,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def generate_structured_with_model_async(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured output asynchronously for parallel execution.

        Args:
            model_name: Exact model name to use
            prompt: Text prompt
            response_schema: Pydantic model for response structure
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters
        """
        model = self._find_model_by_name(model_name)
        provider = self.providers[model.provider]

        if not model.capabilities.json_strict:
            logger.warning(f"Model {model_name} may not have strict JSON support")

        # Use async method if available, fall back to sync wrapped in thread
        if hasattr(provider, "generate_structured_async"):
            return await provider.generate_structured_async(
                model_name=model.name,
                prompt=prompt,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        else:
            # Fall back to sync method in thread for providers without async
            import asyncio

            return await asyncio.to_thread(
                provider.generate_structured,
                model_name=model.name,
                prompt=prompt,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

    def auto_select_model(
        self,
        requirements: CapabilityRequirements,
        model_preference: ModelPreference = "auto",
        preferred_provider: Optional[str] = None,
    ) -> ModelDetails:
        """
        Automatically select the best model based on requirements.

        Selection strategy:
        1. Filter by capability requirements
        2. Apply model preference (local/cloud/auto)
        3. Prefer specific provider if requested
        4. Rank by context window size
        5. Return best match
        """
        all_models = self.list_models()

        # Filter by capabilities
        matching = filter_by_capabilities(all_models, requirements)

        if not matching:
            raise ModelUnavailableError(
                model="auto-select",
                provider="any",
                reason=f"No models match requirements: {requirements.model_dump()}",
            )

        # Apply model preference
        if model_preference == "local":
            local_models = [m for m in matching if m.type == "local"]
            if local_models:
                matching = local_models
            prefer_local = True
        elif model_preference == "cloud":
            matching = [m for m in matching if m.type == "cloud"]
            prefer_local = False
        else:  # auto
            prefer_local = self.config.default_model_preference == "local"

        # Prefer specific provider if requested
        if preferred_provider and preferred_provider in self.providers:
            provider_models = [m for m in matching if m.provider == preferred_provider]
            if provider_models:
                matching = provider_models

        # Find best model
        best = find_best_model(matching, requirements, prefer_local)

        if not best:
            raise ModelUnavailableError(
                model="auto-select",
                provider="any",
                reason="Could not select a suitable model",
            )

        logger.info(f"Auto-selected model: {best.name} ({best.provider})")
        return best

    def generate_auto(
        self,
        prompt: str,
        requirements: Optional[CapabilityRequirements] = None,
        model_preference: ModelPreference = "auto",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate text with automatic model selection.

        Use this when:
        - Backend operation needs a model but user hasn't chosen
        - You want "smart" model selection based on requirements
        """
        # Use basic requirements if not specified
        if requirements is None:
            requirements = CapabilityRequirements(min_context_window=None)

        # Select best model
        model = self.auto_select_model(requirements, model_preference)
        provider = self.providers[model.provider]

        # Generate
        text = provider.generate_text(
            model_name=model.name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return GenerationResult(
            text=text, model=model.name, provider=provider.provider_name
        )

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all providers for monitoring/debugging.
        """
        status = {}

        for name, provider in self.providers.items():
            try:
                is_available = provider.is_available()
                model_count = len(provider.list_models()) if is_available else 0

                status[name] = {
                    "available": is_available,
                    "model_count": model_count,
                    "type": provider.provider_type,
                    "name": provider.provider_name,
                }
            except Exception as e:
                status[name] = {
                    "available": False,
                    "error": str(e),
                    "type": provider.provider_type,
                    "name": name,
                }

        return status
