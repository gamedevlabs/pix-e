"""
Shared utilities for Django views using LLM orchestrator.

Provides common patterns for model ID resolution and error handling.
"""

import logging

from django.http import JsonResponse
from rest_framework import status as http_status

from llm.config import get_config

logger = logging.getLogger(__name__)


def get_model_id(model_name: str) -> str:
    """
    Map frontend model names to actual model IDs using config.

    The frontend sends simplified model names like "gemini" or "openai",
    which are mapped to actual model IDs (e.g., "gemini-2.0-flash-exp", "gpt-4o-mini")
    via the config's model alias system.

    Args:
        model_name: Frontend model name ("gemini", "openai", "ollama")

    Returns:
        Full model ID from config aliases

    Examples:
        >>> get_model_id("gemini")
        "gemini-2.0-flash-exp"

        >>> get_model_id("openai")
        "gpt-4o-mini"
    """
    config = get_config()
    return config.resolve_model_alias(model_name)


def handle_view_error(
    error: Exception,
    operation: str,
    status_code: int = http_status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JsonResponse:
    """
    Handle view errors with proper logging and response formatting.

    Logs the exception with full traceback and returns a properly formatted
    JSON error response.

    Args:
        error: The exception that occurred
        operation: Name of the operation (for logging context)
        status_code: HTTP status code to return (default: 500)

    Returns:
        JsonResponse with error details and appropriate status code

    Examples:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     return handle_view_error(e, "risky_operation", 400)
    """
    logger.exception(f"Error in {operation}: {error}")
    return JsonResponse(
        {"error": str(error)},
        status=status_code,
    )
