"""
OpenTelemetry integration for LLM observability.
Provides instrumentation for tracking token usage, costs, and latencies
across all LLM operations. Integrates with OpenLLMetry for LLM-specific
telemetry.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    trace = None  # type: ignore


class TelemetryConfig:
    """Configuration for telemetry system."""

    def __init__(
        self,
        enabled: bool = False,
        service_name: str = "pix-e-llm",
        export_to_console: bool = False,
    ):
        """Initialize telemetry configuration."""
        self.enabled = enabled and TELEMETRY_AVAILABLE
        self.service_name = service_name
        self.export_to_console = export_to_console


class TelemetryManager:
    """Manages OpenTelemetry instrumentation for LLM operations."""

    def __init__(self, config: Optional[TelemetryConfig] = None):
        """Initialize telemetry manager."""
        self.config = config or TelemetryConfig(enabled=False)
        self.tracer: Optional[Any] = None

        if self.config.enabled:
            self._initialize_tracer()

    def _initialize_tracer(self) -> None:
        """Initialize OpenTelemetry tracer with configured exporters."""
        if not TELEMETRY_AVAILABLE or not trace:
            return

        provider = TracerProvider()

        if self.config.export_to_console:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))

        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(self.config.service_name)

    def create_span(
        self, operation_name: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Create telemetry span for an operation."""
        if not self.config.enabled or not self.tracer:
            return _NoOpSpan()

        span = self.tracer.start_as_current_span(operation_name)
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        return span

    def record_token_usage(
        self, span: Any, prompt_tokens: int, completion_tokens: int, total_tokens: int
    ) -> None:
        """Record token usage in span."""
        if not self.config.enabled or isinstance(span, _NoOpSpan):
            return

        span.set_attribute("llm.usage.prompt_tokens", prompt_tokens)
        span.set_attribute("llm.usage.completion_tokens", completion_tokens)
        span.set_attribute("llm.usage.total_tokens", total_tokens)

    def record_cost(self, span: Any, cost: float, currency: str = "USD") -> None:
        """Record estimated cost in span."""
        if not self.config.enabled or isinstance(span, _NoOpSpan):
            return

        span.set_attribute("llm.cost.amount", cost)
        span.set_attribute("llm.cost.currency", currency)

    def instrument_call(
        self, operation_name: str, model_name: str, provider: str
    ) -> Callable:
        """Decorator to instrument LLM provider calls."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self.config.enabled:
                    return func(*args, **kwargs)

                attributes = {
                    "llm.model": model_name,
                    "llm.provider": provider,
                    "llm.operation": operation_name,
                }

                with self.create_span(f"llm.{operation_name}", attributes) as span:
                    start_time = time.time()

                    try:
                        result = func(*args, **kwargs)
                        span.set_attribute("llm.success", True)
                        return result
                    except Exception as e:
                        span.set_attribute("llm.success", False)
                        span.set_attribute("llm.error", str(e))
                        raise
                    finally:
                        latency_ms = int((time.time() - start_time) * 1000)
                        span.set_attribute("llm.latency_ms", latency_ms)

            return wrapper

        return decorator


class _NoOpSpan:
    """No-op span for when telemetry is disabled."""

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def set_attribute(self, key: str, value: Any) -> None:
        pass


# Global telemetry manager instance
_telemetry_manager: Optional[TelemetryManager] = None


def get_telemetry_manager() -> TelemetryManager:
    """Get global telemetry manager instance."""
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager


def initialize_telemetry(config: TelemetryConfig) -> None:
    """Initialize global telemetry with configuration."""
    global _telemetry_manager
    _telemetry_manager = TelemetryManager(config)
