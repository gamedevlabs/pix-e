"""
Shared helpers for pillars views.
"""

import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import Http404, JsonResponse
from rest_framework.exceptions import APIException as _DRFException

from accounts.models import UserApiKey
from accounts.views import should_auto_disable as _should_auto_disable
from game_concept.models import GameConcept
from game_concept.utils import get_current_game_concept, get_current_project
from llm.exceptions import AuthenticationError, OrchestratorError, ProviderError
from pillars.models import Pillar
from pillars.utils import format_pillars_text

logger = logging.getLogger(__name__)

# Provider names in error context → UserApiKey.provider values.
# The OpenAI provider class sets provider="openai" in errors, but user keys
# using the same SDK may be stored as "custom" or "morpheus".
_PROVIDER_KEY_MAP: dict[str, list[str]] = {
    "openai": ["openai", "custom", "morpheus"],
    "gemini": ["gemini"],
}


def _disable_keys_for_provider(request, provider: str) -> int:
    """Set is_active=False + disabled_reason for all active keys of a provider."""
    mapped_providers = _PROVIDER_KEY_MAP.get(provider, [provider])
    return UserApiKey.objects.filter(
        user=request.user, provider__in=mapped_providers, is_active=True
    ).update(is_active=False, disabled_reason="auth_failure")


def handle_orchestrator_error(request, e: Exception) -> JsonResponse:
    """
    Handle LLM orchestrator errors consistently, auto-disabling invalid keys.

    Returns a JsonResponse with an appropriate HTTP status and user-facing
    message instead of a cryptic 500.
    """
    # Extract provider from exception context if available
    provider = ""
    if isinstance(e, AuthenticationError):
        provider = e.context.get("provider", "")
    elif isinstance(e, ProviderError):
        provider = e.context.get("provider", "")
        # Also check the message for auth keywords as fallback
        msg = str(e)
        provider_in_msg = ""
        for p in ["openai", "gemini"]:
            if f"provider '{p}'" in msg.lower():
                provider_in_msg = p
                break
        provider = provider or provider_in_msg

    # Auto-disable if we know the provider and the error looks like auth failure
    if provider and provider != "none":
        is_auth = isinstance(e, AuthenticationError) or (
            isinstance(e, ProviderError) and _should_auto_disable(str(e))
        )
        if is_auth:
            count = _disable_keys_for_provider(request, provider)
            if count:
                logger.warning(
                    "Auto-disabled %d %s API key(s) for user %s: %s",
                    count, provider, request.user.id, str(e)[:120],
                )
            return JsonResponse(
                {
                    "error": "Your API key is invalid and has been disabled. "
                    "Please re-add it in Settings.",
                },
                status=401,
            )

    if isinstance(e, OrchestratorError):
        msg = str(e)
        if "No LLM providers available" in msg:
            return JsonResponse(
                {
                    "error": "No valid API keys configured. "
                    "Please add an API key in Settings to use AI features.",
                },
                status=400,
            )

    if isinstance(e, _DRFException):
        raise

    if isinstance(e, Http404):
        return JsonResponse({"error": str(e)}, status=404)

    logger.exception("Error in LLM operation")
    return JsonResponse({"error": str(e)}, status=500)


def get_project_pillars(user: User) -> QuerySet[Pillar]:
    project = get_current_project(user)
    queryset = Pillar.objects.filter(user=user)
    if project:
        return queryset.filter(project=project)
    return queryset.filter(project__isnull=True)


def get_project_concept(user: User) -> Optional[GameConcept]:
    project = get_current_project(user)
    return get_current_game_concept(project)


def build_context_payload(
    pillars: list[Pillar], game_concept: GameConcept
) -> tuple[str, str]:
    return format_pillars_text(pillars), game_concept.content


def build_context_payload_from_text(
    pillars: list[Pillar], context_text: str
) -> tuple[str, str]:
    return format_pillars_text(pillars), context_text
