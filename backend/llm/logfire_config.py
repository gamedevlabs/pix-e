"""
Logfire configuration for LLM observability.

Sets up automatic instrumentation for OpenAI and Gemini providers.
"""

import os

import logfire

_configured = False


def configure_logfire(service_name: str = "pix-e-backend") -> None:
    """
    Configure Logfire with provider instrumentation.

    This should be called once at application startup (in settings.py).

    Args:
        service_name: Name of the service for Logfire tracking
    """
    global _configured

    if _configured:
        return

    logfire.configure(
        service_name=service_name,
        console=False,
    )

    logfire.instrument_openai()

    os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")
    logfire.instrument_google_genai()

    # Instrument Django
    logfire.instrument_django()

    _configured = True


def get_logfire():
    """Get logfire instance for manual span creation."""
    return logfire
