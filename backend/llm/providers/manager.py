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
        """
        Initialize the model manager.

        Args:
            config: Configuration instance (uses default if not provided)
        """
        self.config = config or get_config()
        # providers maps provider_name → provider_instance (backward compat)
        self.providers: Dict[str, BaseProvider] = {}
        # _provider_list maps provider_name → list of provider instances
        self._provider_list: Dict[str, List[BaseProvider]] = {}
        # _model_registry maps model_name → provider_instance for O(1) lookup
        self._model_registry: Dict[str, BaseProvider] = {}
        self._registry_built: bool = False  # lazy-build flag; see _ensure_registry()
        self._model_cache: Optional[List[ModelDetails]] = None
        self._cache_timestamp: Optional[float] = None

        # Initialize all available providers
        self._init_providers()

    # ============================================
    # Factory Methods for Per-User Keys
    # ============================================

    @classmethod
    def for_user(cls, user, enc_key: bytes) -> "ModelManager":
        """
        Create a ModelManager that uses ALL of the given user's active API keys.

        Providers are built dynamically from ``UserApiKey`` rows.  If the
        user has no configured keys the manager falls back to env-var
        providers (global config).  Ollama is always added from env config
        when available.

        Args:
            user: The Django user whose API keys should be loaded.
            enc_key: Fernet encryption key bytes from the user's session
                (obtained via ``get_encryption_key_from_session``).

        Returns:
            A new ``ModelManager`` instance backed by the user's API keys
            (or env-var fallback).

        Raises:
            ProviderError: If no providers could be initialised at all.
        """
        from llm.providers.user_providers import create_providers_for_user

        manager = cls.__new__(cls)
        manager.config = get_config()
        manager.providers = {}
        manager._model_registry = {}
        manager._registry_built = False
        manager._provider_list = {}
        manager._model_cache = None
        manager._cache_timestamp = None

        # Load user's keys as provider instances
        # NOTE: _rebuild_model_registry is NOT called here — it's lazy via
        # _ensure_registry(). This avoids live network calls on every request.
        user_providers = create_providers_for_user(user, enc_key)
        manager._provider_list.update(user_providers)

        # Fallback: if no user keys, try env-var providers
        has_user_keys = any(
            providers
            for name, providers in manager._provider_list.items()
            if name != "ollama" and providers
        )
        if not has_user_keys:
            logger.info("No user API keys found — falling back to env-var providers")
            manager._init_providers()
        else:
            # Ensure Ollama is added from config if not already present
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
                        # Registry will be lazily built on first use
                        # (see _ensure_registry)
                    else:
                        logger.debug("Ollama not available, skipping")
                except Exception:
                    logger.debug("Ollama not available, skipping")

        if not manager._provider_list:
            raise ProviderError(
                message="No LLM providers available. Add an API key in Settings.",
                provider="none",
            )

        # Sync backward compat providers map
        manager._sync_providers_map()

        return manager

    @classmethod
    def for_user_and_key(cls, user, api_key_id: str, enc_key: bytes) -> "ModelManager":
        """
        Create a ModelManager scoped to a SINGLE specific API key.

        Only the provider that corresponds to the requested key is loaded
        (plus Ollama if reachable).  This is useful when the user explicitly
        picks one of their saved keys from the UI.

        Args:
            user: The Django user who owns the key.
            api_key_id: The primary key of the ``UserApiKey`` record.
            enc_key: Fernet encryption key bytes from the user's session.

        Returns:
            A new ``ModelManager`` instance with exactly one provider.

        Raises:
            django.http.Http404: If the ``UserApiKey`` does not exist or
                is not owned by ``user``.
            ProviderError: If the resulting manager has no providers.
        """
        from accounts.models import UserApiKey
        from accounts.encryption import decrypt_api_key
        from llm.providers.user_providers import _create_provider

        from django.http import Http404

        try:
            api_key_obj = UserApiKey.objects.get(id=api_key_id, user=user, is_active=True)
        except UserApiKey.DoesNotExist:
            # Check if the key exists but was disabled — give a helpful message
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
            # Registry lazily built on first use (see _ensure_registry)

        # Add Ollama only if available
        try:
            ollama = OllamaProvider(
                {
                    "base_url": manager.config.ollama_base_url,
                    "timeout": manager.config.ollama_timeout_seconds,
                }
            )
            if ollama.is_available():
                manager._provider_list.setdefault("ollama", []).append(ollama)
                # Registry lazily built on first use (see _ensure_registry)
            else:
                logger.debug("Ollama not available, skipping")
        except Exception:
            logger.debug("Ollama not available, skipping")

        manager._sync_providers_map()

        return manager

    # ============================================
    # Internal Helpers
    # ============================================

    def _ensure_registry(self) -> None:
        """Build the model registry lazily on first use.

        Called before any registry lookup. Avoids network calls at
        initialization time, which is important because ``for_user()``
        is called on every view that needs an orchestrator.
        """
        if not self._registry_built:
            self._rebuild_model_registry()
            self._registry_built = True

    def _rebuild_model_registry(self) -> None:
        """
        Rebuild the ``model_name → provider_instance`` lookup table.

        Iterates over all provider instances in ``_provider_list``, calls
        ``list_models()`` on each, and indexes every returned model by
        name.  The first provider that advertises a given name wins (FIFO
        ordering within ``_provider_list``).

        Note: This makes live network calls to each provider. It is called
        lazily via ``_ensure_registry()`` — not at construction time — so
        creating a ``ModelManager`` is instant.
        """
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
        """Sync backward-compat .providers dict from _provider_list."""
        self.providers = {}
        for name, plist in self._provider_list.items():
            if plist:
                self.providers[name] = plist[0]

    def _init_providers(self) -> None:
        """
        Initialize all configured LLM providers from env config.

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
                self._provider_list.setdefault("ollama", []).append(ollama)
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
                    self._provider_list.setdefault("openai", []).append(openai)
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
                    self._provider_list.setdefault("gemini", []).append(gemini)
                    logger.info("✅ Gemini provider initialized")
                else:
                    logger.warning("⚠️  Gemini provider not available")
            except Exception as e:
                logger.warning(f"⚠️  Gemini provider initialization failed: {e}")
        else:
            logger.info("⚠️  Gemini API key not configured")

        self._rebuild_model_registry()

        # Ensure at least one provider is available
        if not self.providers:
            raise ProviderError(
                message="No LLM providers available. Configure at least one provider (Ollama, OpenAI, or Gemini).",  # noqa: E501
                provider="none",
            )

        provider_names = ", ".join(self.providers.keys())
        logger.info(
            f"📊 Initialized {len(self.providers)} provider(s): {provider_names}"
        )

    # ============================================
    # Model Listing
    # ============================================

    def list_models(self, refresh: bool = False) -> List[ModelDetails]:
        """
        List all available models from every provider instance.

        Iterates over ``_provider_list`` (which may contain multiple
        instances per provider name, e.g. several OpenAI keys).  Results
        are cached for ``cache_ttl_seconds``; call with ``refresh=True`` to
        bypass the cache.

        Args:
            refresh: If ``True``, ignore the cache and re-fetch models
                from all providers.

        Returns:
            A list of ``ModelDetails``, deduplicated by model name.
        """
        now = time.time()

        if (
            not refresh
            and self._model_cache is not None
            and self._cache_timestamp is not None
            and self.config.cache_enabled
            and now - self._cache_timestamp < self.config.cache_ttl_seconds
        ):
            return self._model_cache

        # Fetch models from all provider instances
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

        if provider_filter:
            models = [m for m in models if m.provider == provider_filter]

        if capability_filter:
            models = filter_by_capabilities(models, capability_filter)

        return models

    def get_model_inventory(self, refresh: bool = False) -> ModelInventory:
        """
        Get complete model inventory matching API spec.
        """
        models = self.list_models(refresh=refresh)
        return ModelInventory(models=models)

    # ============================================
    # Model Resolution
    # ============================================

    def _find_model_by_name(self, model_name: str) -> Tuple[ModelDetails, BaseProvider]:
        """
        Resolve a model name to its details and provider instance.

        Uses ``_model_registry`` for O(1) lookup — does **not** iterate all
        providers.  When the manager was created via ``for_user_and_key``,
        the registry only contains models from that single key, making the
        lookup naturally scoped.

        Args:
            model_name: The name of the model to look up.

        Returns:
            A ``(ModelDetails, BaseProvider)`` tuple.

        Raises:
            ModelUnavailableError: If the model name is not found in any
                provider's model list.
        """
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

        # Get model details from provider
        models = provider.list_models()
        for model in models:
            if model.name == model_name:
                return model, provider

        raise ModelUnavailableError(
            model=model_name,
            provider=provider.provider_name,
            reason=f"Model '{model_name}' not found in provider's model list",
        )

    # ============================================
    # Generation Methods
    # ============================================

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

        Uses _model_registry for O(1) model-to-provider resolution.
        This works correctly with both single-key and multi-key ModelManagers.
        """
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
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Generate structured output using a specific model (user-selected).
        """
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

    def auto_select_model(
        self,
        requirements: CapabilityRequirements,
        model_preference: ModelPreference = "auto",
        preferred_provider: Optional[str] = None,
    ) -> ModelDetails:
        """
        Automatically select the best model based on requirements.
        """
        # Get models from registry
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
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> GenerationResult:
        """
        Generate text with automatic model selection.
        """
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
