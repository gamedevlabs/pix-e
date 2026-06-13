try:
    from opentelemetry import trace

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    trace = None  # type: ignore

from django.core.cache import cache
from django.utils import timezone


BACKEND_LOG_TTL_SECONDS = 60 * 60 * 2
MAX_BACKEND_LOG_ENTRIES = 100

def get_trace_ids():
    span_context = trace.get_current_span().get_span_context()

    if not span_context.is_valid:
        return "", ""

    return f"{span_context.trace_id:032x}", f"{span_context.span_id:016x}"

def backend_log_cache_key(session_id):
    return f"helpdesk:backend-session-logs:{session_id}"


def buffer_backend_session_log(
        *,
        session_id,
        level,
        event,
        message="",
        request=None,
        status_code=None,
        metadata=None,
):
    if not session_id:
        return

    trace_id, span_id = get_trace_ids()

    entry = {
        "time": timezone.now().isoformat(),
        "level": level,
        "event": event,
        "message": message,
        "method": getattr(request, "method", ""),
        "path": getattr(request, "path", ""),
        "status_code": status_code,
        "trace_id": trace_id,
        "span_id": span_id,
        "metadata": metadata or {},
    }

    key = backend_log_cache_key(session_id)
    entries = cache.get(key, [])
    entries.append(entry)

    cache.set(
        key,
        entries[-MAX_BACKEND_LOG_ENTRIES:],
        timeout=BACKEND_LOG_TTL_SECONDS,
    )


def pop_backend_session_logs(session_id):
    key = backend_log_cache_key(session_id)
    entries = cache.get(key, [])
    cache.delete(key)
    return entries