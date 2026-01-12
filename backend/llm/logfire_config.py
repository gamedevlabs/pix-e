"""
Logfire configuration for LLM observability.
Sets up automatic instrumentation for OpenAI and Gemini providers.
"""

import os
from typing import Any

# Type stubs for when logfire is not available
logfire: Any = None
LogfireConfigError: type[Exception] = Exception


class _NoOpLogfire:
    """No-op logfire object when logfire is not installed."""

    def configure(self, *args: Any, **kwargs: Any) -> None:
        pass

    def instrument_openai(self) -> None:
        pass

    def instrument_google_genai(self) -> None:
        pass

    def instrument_django(self) -> None:
        pass

    def span(self, *args: Any, **kwargs: Any) -> Any:
        return _NoOpSpan()

    def info(self, *args: Any, **kwargs: Any) -> None:
        pass

    def warn(self, *args: Any, **kwargs: Any) -> None:
        pass

    def exception(self, *args: Any, **kwargs: Any) -> None:
        pass


class _NoOpSpan:
    """No-op span context manager."""

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


_noop_logfire = _NoOpLogfire()

try:
    import logfire as _logfire_module  # type: ignore[import-untyped]
    from logfire.exceptions import (
        LogfireConfigError as _LogfireConfigError,  # type: ignore[import-untyped]
    )

    logfire = _logfire_module  # type: ignore[assignment]
    LogfireConfigError = _LogfireConfigError  # type: ignore[assignment]
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


_configured = False


def configure_logfire(service_name: str = "pix-e-backend") -> None:
    """
    Configure Logfire with provider instrumentation.
    This should be called once at application startup (in settings.py).
    Gracefully handles cases where logfire is not installed or not authenticated.
    Args:
        service_name: Name of the service for Logfire tracking
    """
    global _configured

    if _configured:
        return

    if not LOGFIRE_AVAILABLE:
        _configured = True
        return

    try:
        logfire.configure(
            service_name=service_name,
            console=False,
        )

        logfire.instrument_openai()

        os.environ.setdefault(
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true"
        )
        logfire.instrument_google_genai()

        logfire.instrument_django()

        _configured = True
    except LogfireConfigError:
        _configured = True
    except Exception:
        _configured = True


def get_logfire():
    """
    Get logfire instance for manual span creation.
    Returns a no-op object if logfire is not available or not configured.
    """
    if not LOGFIRE_AVAILABLE or logfire is None:
        return _noop_logfire
    return logfire
