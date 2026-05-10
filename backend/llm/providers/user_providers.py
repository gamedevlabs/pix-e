"""
Dynamically create providers based on a user's stored API keys.

Each provider is created with a decrypted API key derived from the user's
session-derived encryption key (from their login password).
"""

import logging
from typing import Dict, List, Optional

from django.contrib.auth import get_user_model

from accounts.constants import PROVIDER_DEFAULT_BASE_URLS
from accounts.encryption import decrypt_api_key
from accounts.models import UserApiKey
from llm.providers.base import BaseProvider
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.ollama_provider import OllamaProvider
from llm.providers.openai_provider import OpenAIProvider

User = get_user_model()
logger = logging.getLogger(__name__)


def create_providers_for_user(
    user: User, enc_key: bytes
) -> Dict[str, List[BaseProvider]]:
    """
    Create provider instances for all active API keys belonging to a user.

    Decrypts each stored key using the session-derived ``enc_key`` and
    instantiates the appropriate provider class.  Ollama is also added
    automatically when the local server is reachable.

    Args:
        user: The Django user whose keys should be loaded.
        enc_key: Fernet encryption key bytes derived from the user's
            session password (via ``accounts.encryption``).

    Returns:
        A dictionary mapping provider names (e.g. ``"openai"``,
        ``"gemini"``) to lists of ``BaseProvider`` instances.  May be
        empty if no keys could be decrypted or no provider could be
        initialised.
    """
    providers: Dict[str, List[BaseProvider]] = {}

    api_keys = UserApiKey.objects.filter(user=user, is_active=True).select_related(
        "user"
    )

    for api_key in api_keys:
        try:
            raw_key = decrypt_api_key(api_key.encrypted_key, enc_key)
        except Exception as e:
            logger.error(f"Failed to decrypt key {api_key.id} for user {user.id}: {e}")
            continue

        provider = _create_provider(api_key.provider, raw_key, api_key.base_url)
        if provider:
            provider_name = api_key.provider
            if provider_name not in providers:
                providers[provider_name] = []
            providers[provider_name].append(provider)

    # Add Ollama only if available (local, no key needed)
    try:
        ollama = OllamaProvider(
            {
                "base_url": "http://localhost:11434",
                "timeout": 5,  # short timeout — skip quickly if unreachable
            }
        )
        if ollama.is_available():
            providers.setdefault("ollama", []).append(ollama)
        else:
            logger.debug("Ollama not available, skipping")
    except Exception as e:
        logger.debug(f"Ollama not available: {e}")

    return providers


def _create_provider(
    provider_type: str,
    api_key: str,
    base_url: str = "",
) -> Optional[BaseProvider]:
    """
    Create a single provider instance from a decrypted API key.

    Args:
        provider_type: One of ``"openai"``, ``"custom"``, ``"morpheus"``,
            or ``"gemini"``.
        api_key: The decrypted API key string.
        base_url: Optional custom base URL for the provider's API.

    Returns:
        A ``BaseProvider`` instance, or ``None`` if the provider type is
        unknown or initialisation fails.
    """
    try:
        if provider_type in ("openai", "custom", "morpheus"):
            config = {"api_key": api_key, "timeout": 30}
            effective_url = base_url or PROVIDER_DEFAULT_BASE_URLS.get(
                provider_type, ""
            )
            if effective_url:
                config["base_url"] = effective_url
            if provider_type in ("morpheus", "custom"):
                config["include_all_models"] = True
            return OpenAIProvider(config)

        elif provider_type == "gemini":
            return GeminiProvider({"api_key": api_key, "timeout": 30})

        else:
            logger.warning(f"Unknown provider type: {provider_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to create provider {provider_type}: {e}")
        return None
