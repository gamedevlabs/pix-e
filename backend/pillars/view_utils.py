"""
Shared helpers for pillars views.

Includes project/context helpers and orchestrator error handling
for per-user API key integration.
"""

import logging
from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import JsonResponse

from accounts.models import UserApiKey
from game_concept.models import GameConcept
from game_concept.utils import get_current_game_concept
from llm.exceptions import OrchestratorError, ProviderError, RateLimitError
from pillars.models import Pillar
from pillars.utils import format_pillars_text
from projects.utils import get_current_project

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
#  Project / concept helpers
# ─────────────────────────────────────────────


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


# ─────────────────────────────────────────────
#  Orchestrator error handling
# ─────────────────────────────────────────────


# Authentication-failure patterns — matches what accounts/views.py uses
RATE_LIMIT_PATTERNS: list[str] = [
    "429",
    "too many requests",
    "rate limit",
    "rate_limit",
    "resource_exhausted",
    "quota exceeded",
    "requests per minute",
]

AUTH_FAILURE_PATTERNS: list[str] = [
    "http 401",
    "http 403",
    "status 401",
    "status 403",
    "401 unauthorized",
    "403 forbidden",
    "unauthorized",
    "forbidden",
    "invalid api key",
    "authentication failed",
    "permission denied",
    "not authorized",
    "auth error",
    "invalid authentication credentials",
    "api key not found",
    "credential",
]


def _disable_keys_for_provider(user: User, provider: str) -> None:
    """
    Disable all active UserApiKey records for a user+provider combination.

    Called when the provider rejects a key with an auth error during
    an LLM call (not during a manual test). The user can re-enable
    keys from the Settings UI after fixing the credentials.
    """
    updated = UserApiKey.objects.filter(
        user=user,
        provider=provider,
        is_active=True,
    ).update(is_active=False, disabled_reason="auth_failure")
    if updated:
        logger.warning(
            "Auto-disabled %d API key(s) for user=%s provider=%s",
            updated,
            user.id,
            provider,
        )


def handle_orchestrator_error(
    exception: Exception,
    user: User,
    provider: Optional[str] = None,
    model: str = "",
) -> JsonResponse:
    """
    Map an orchestrator/ProviderError to a user-facing JSON response.

    * ProviderError with rate-limit patterns → return 429 with switch-model suggestion.
    * ProviderError with auth-failure patterns → auto-disable the key(s) and return 401.
    * All other errors → log and return 500 with a generic message.

    Returns a JsonResponse so callers can ``return handle_orchestrator_error(...)``.
    """
    provider_name = provider or _guess_provider_from_error(str(exception))
    model_suffix = f" ({model})" if model else ""

    # RateLimitError — specific type from LLM providers
    if isinstance(exception, RateLimitError):
        logger.warning(
            "Rate limited on provider=%s for user=%s",
            provider_name,
            user.id,
        )
        return JsonResponse(
            {
                "error": "rate_limited",
                "provider": provider_name,
                "model": model,
                "detail": (
                    f"{provider_name.title()}{model_suffix} rate limited — "
                    "try switching to a different model or provider"
                ),
            },
            status=429,
        )

    if isinstance(exception, ProviderError):
        error_text = str(exception).lower()

        # Rate limit — don't disable keys, suggest model switch
        if any(patt in error_text for patt in RATE_LIMIT_PATTERNS):
            logger.warning(
                "Rate limited on provider=%s for user=%s",
                provider_name,
                user.id,
            )
            return JsonResponse(
                {
                    "error": "rate_limited",
                    "provider": provider_name,
                    "model": model,
                    "detail": (
                        f"{provider_name.title()}{model_suffix} rate limited — "
                        "try switching to a different model or provider"
                    ),
                },
                status=429,
            )

        # Auth failure — auto-disable keys
        if any(patt in error_text for patt in AUTH_FAILURE_PATTERNS):
            _disable_keys_for_provider(user, provider_name)
            return JsonResponse(
                {
                    "error": (
                        "API key rejected by provider. "
                        "It has been disabled — check your settings."
                    ),
                },
                status=401,
            )
        return JsonResponse(
            {"error": f"Provider error: {exception}"},
            status=502,
        )

    # Any other OrchestratorError (e.g. timeout, model unavailable)
    if isinstance(exception, OrchestratorError):
        return JsonResponse(
            {"error": f"LLM error: {exception}"},
            status=502,
        )

    logger.exception("Unhandled orchestrator error: %s", exception)
    return JsonResponse(
        {"error": "An unexpected error occurred while processing your request."},
        status=500,
    )


def _guess_provider_from_error(error_text: str) -> str:
    """Best-effort provider name from error text."""
    text = error_text.lower()
    if "gemini" in text or "google" in text:
        return "gemini"
    if "openai" in text or "gpt" in text:
        return "openai"
    return "provider"
