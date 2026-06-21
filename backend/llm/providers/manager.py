"""
Model Manager for the LLM Orchestrator.

Central manager that handles:
- Provider initialization and lifecycle
- Model aggregation from all providers
- Direct model selection (user-specified)
- Automatic model selection (based on requirements)
- Fallback and retry logic
- Per-user API key support
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

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

    Supports three creation paths:

    1. **Global / env-var based** (``ModelManager()``) — reads API keys
       from environment variables via ``Config``.
    2. **Per-user, all keys** (``ModelManager.for_user(user, enc_key)``) —
       loads every active ``UserApiKey`` for the given user.
    3. **Per-user, single key** (``ModelManager.for_user_and_key(user, api_key_id, enc_key)``)  —  # noqa: E501
       loads exactly one ``UserApiKey``.

    Model resolution uses a ``_model_registry`` (``model_name → provider_instance``)
    for O(1) lookup, supporting multiple providers with the same model name.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.providers: Dict[str, BaseProvider] = {}
        self._provider_list: Dict[str, List[BaseProvider]] = {}
        self._model_registry: Dict[str, BaseProvider] = {}
        self._registry_built: bool = False
        self._model_cache: Optional[List[ModelDetails]] = None
        self._cache_timestamp: Optional[float] = None

        self._init_env_providers()

    def _init_env_providers(self) -> None:
        try:
            ollama = OllamaProvider(
                {
                    "base_url": self.config.ollama_base_url,
                    "timeout": self.config.ollama_timeout_seconds,
                }
            )
            if ollama.is_available():
                self._provider_list.setdefault("ollama", []).append(ollama)
                self.providers["ollama"] = ollama
                logger.info("Ollama provider initialized")
            else:
                logger.info("Ollama provider not available")
        except Exception as e:
            logger.warning(f"Ollama provider initialization failed: {e}")

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
                    self._provider_list.setdefault("openai", []).append(openai)
                    self.providers["openai"] = openai
                    logger.info("OpenAI provider initialized")
                else:
                    logger.warning("OpenAI provider not available")
            except Exception as e:
                logger.warning(f"OpenAI provider initialization failed: {e}")
        else:
            logger.info("OpenAI API key not configured")

        if self.config.gemini_api_key:
            try:
                gemini = GeminiProvider(
                    {
                        "api_key": self.config.gemini_api_key,
                        "timeout": self.config.gemini_timeout_seconds,
                    }
                )
                if gemini.is_available():
                    self._provider_list.setdefault("gemini", []).append(gemini)
                    self.providers["gemini"] = gemini
                    logger.info("Gemini provider initialized")
                else:
                    logger.warning("Gemini provider not available")
            except Exception as e:
                logger.warning(f"Gemini provider initialization failed: {e}")
        else:
            logger.info("Gemini API key not configured")

    @classmethod
    def for_user(cls, user, enc_key: bytes) -> "ModelManager":
        from llm.providers.user_providers import create_providers_for_user

        manager = cls.__new__(cls)
        manager.config = get_config()
        manager.providers = {}
        manager._model_registry = {}
        manager._registry_built = False
        manager._provider_list = {}
        manager._model_cache = None
        manager._cache_timestamp = None

        user_providers = create_providers_for_user(user, enc_key)
        manager._provider_list.update(user_providers)

        has_user_keys = any(
            providers
            for name, providers in manager._provider_list.items()
            if name != "ollama" and providers
        )
        if not has_user_keys:
            raise ProviderError(
                message="No valid API keys configured. Add an API key in Settings.",
                provider="none",
            )
        else:
            if "ollama" not in manager._provider_list:
                try:
                    ollama = OllamaProvider(
                        {
                            "base_url": manager.config.ollama_base_url,
                            "timeout": manager.config.ollama_timeout_seconds,
                        }
                    )
                    if ollama.is_available():
                        manager._provider_list.setdefault("ollama", []).append(ollama)
                    else:
                        logger.debug("Ollama not available, skipping")
                except Exception:
                    logger.debug("Ollama not available, skipping")

        if not manager._provider_list:
            raise ProviderError(
                message="No LLM providers available. Add an API key in Settings.",
                provider="none",
            )

        manager._sync_providers_map()
        return manager

    @classmethod
    def for_user_and_key(cls, user, api_key_id: str, enc_key: bytes) -> "ModelManager":
        from django.http import Http404

        from accounts.encryption import decrypt_api_key
        from accounts.models import UserApiKey
        from llm.providers.user_providers import _create_provider

        try:
            api_key_obj = UserApiKey.objects.get(
                id=api_key_id, user=user, is_active=True
            )
        except UserApiKey.DoesNotExist:
            try:
                disabled_key = UserApiKey.objects.get(id=api_key_id, user=user)
            except UserApiKey.DoesNotExist:
                raise Http404("API key not found.")
            if disabled_key.disabled_reason == "auth_failure":
                raise Http404(
                    "This API key was disabled because the provider rejected it. "
                    "Re-enter a valid key in Settings to re-enable it."
                )
            raise Http404("API key is disabled.")
        raw_key = decrypt_api_key(api_key_obj.encrypted_key, enc_key)

        manager = cls.__new__(cls)
        manager.config = get_config()
        manager.providers = {}
        manager._model_registry = {}
        manager._registry_built = False
        manager._provider_list = {}
        manager._model_cache = None
        manager._cache_timestamp = None

        provider = _create_provider(api_key_obj.provider, raw_key, api_key_obj.base_url)
        if provider:
            manager._provider_list[api_key_obj.provider] = [provider]

        try:
            ollama = OllamaProvider(
                {
                    "base_url": manager.config.ollama_base_url,
                    "timeout": manager.config.ollama_timeout_seconds,
                }
            )
            if ollama.is_available():
                manager._provider_list.setdefault("ollama", []).append(ollama)
            else:
                logger.debug("Ollama not available, skipping")
        except Exception:
            logger.debug("Ollama not available, skipping")

        manager._sync_providers_map()
        return manager

    def _ensure_registry(self) -> None:
        if not self._registry_built:
            self._rebuild_model_registry()
            self._registry_built = True

    def _rebuild_model_registry(self) -> None:
        self._model_registry = {}
        for provider_name, provider_list in self._provider_list.items():
            for provider in provider_list:
                try:
                    models = provider.list_models()
                    for model in models:
                        if model.name not in self._model_registry:
                            self._model_registry[model.name] = provider
                except Exception as e:
                    logger.warning(f"Failed to list models from {provider_name}: {e}")

    def _sync_providers_map(self) -> None:
        self.providers = {}
        for name, plist in self._provider_list.items():
            if plist:
                self.providers[name] = plist[0]

    def list_models(self, refresh: bool = False) -> List[ModelDetails]:
        now = time.time()

        if (
            not refresh
            and self._model_cache is not None
            and self._cache_timestamp is not None
            and self.config.cache_enabled
            and now - self._cache_timestamp < self.config.cache_ttl_seconds
        ):
            return self._model_cache

        all_models = []
        seen_model_names = set()
        for provider_name, provider_list in self._provider_list.items():
            for provider in provider_list:
                try:
                    models = provider.list_models()
                    for model in models:
                        if model.name not in seen_model_names:
                            all_models.append(model)
                            seen_model_names.add(model.name)
                except Exception as e:
                    logger.warning(f"Failed to list models from {provider_name}: {e}")

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
        models = self.list_models(refresh=refresh)

        if provider_filter:
            models = [m for m in models if m.provider == provider_filter]

        if capability_filter:
            models = filter_by_capabilities(models, capability_filter)

        return models

    def get_model_inventory(self, refresh: bool = False) -> ModelInventory:
        models = self.list_models(refresh=refresh)
        return ModelInventory(models=models)

    def _find_model_by_name(self, model_name: str) -> Tuple[ModelDetails, BaseProvider]:
        self._ensure_registry()
        provider = self._model_registry.get(model_name)
        if not provider:
            available_names = list(self._model_registry.keys())[:5]
            available_str = ", ".join(available_names) if available_names else "none"
            raise ModelUnavailableError(
                model=model_name,
                provider="unknown",
                reason=f"Model '{model_name}' not found. Available: {available_str}...",
            )

        models = provider.list_models()
        for model in models:
            if model.name == model_name:
                return model, provider

        raise ModelUnavailableError(
            model=model_name,
            provider=provider.provider_name,
            reason=f"Model '{model_name}' not found in provider's model list",
        )

    def generate_with_model(
        self,
        model_name: str,
        prompt: str,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        model_details, provider = self._find_model_by_name(model_name)

        text = provider.generate_text(
            model_name=model_details.name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return GenerationResult(
            text=text, model=model_details.name, provider=provider.provider_name
        )

    def generate_structured_with_model(
        self,
        model_name: str,
        prompt: str,
        response_schema: type,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        model_details, provider = self._find_model_by_name(model_name)

        if not model_details.capabilities.json_strict:
            logger.warning(f"Model {model_name} may not have strict JSON support")

        return provider.generate_structured(
            model_name=model_details.name,
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
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        model_details, provider = self._find_model_by_name(model_name)

        if not model_details.capabilities.json_strict:
            logger.warning(f"Model {model_name} may not have strict JSON support")

        if hasattr(provider, "generate_structured_async"):
            return await provider.generate_structured_async(
                model_name=model_details.name,
                prompt=prompt,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
        else:
            import asyncio

            return await asyncio.to_thread(
                provider.generate_structured,
                model_name=model_details.name,
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
        models = self.list_models()

        matching = filter_by_capabilities(models, requirements)

        if not matching:
            raise ModelUnavailableError(
                model="auto-select",
                provider="any",
                reason=f"No models match requirements: {requirements.model_dump()}",
            )

        if model_preference == "local":
            local_models = [m for m in matching if m.type == "local"]
            if local_models:
                matching = local_models
            prefer_local = True
        elif model_preference == "cloud":
            matching = [m for m in matching if m.type == "cloud"]
            prefer_local = False
        else:
            prefer_local = self.config.default_model_preference == "local"

        if preferred_provider:
            provider_models = [m for m in matching if m.provider == preferred_provider]
            if provider_models:
                matching = provider_models

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
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        if requirements is None:
            requirements = CapabilityRequirements(min_context_window=None)

        model = self.auto_select_model(requirements, model_preference)
        self._ensure_registry()
        provider_info = self._model_registry.get(model.name)

        if not provider_info:
            raise ProviderError(
                message=f"Provider for model '{model.name}' not found in registry",
                provider="unknown",
            )

        text = provider_info.generate_text(
            model_name=model.name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return GenerationResult(
            text=text, model=model.name, provider=provider_info.provider_name
        )

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
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
