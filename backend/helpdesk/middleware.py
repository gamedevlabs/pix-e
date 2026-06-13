import time

try:
    from opentelemetry import trace

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False
    trace = None  # type: ignore

from .session_logging import buffer_backend_session_log


class PixeSessionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_id = request.headers.get("X-Pixe-Session-Id", "").strip()
        request.pixe_session_id = session_id

        span = trace.get_current_span()
        if session_id and span.is_recording():
            span.set_attribute("pixe.session_id", session_id)

        started_at = time.monotonic()

        try:
            response = self.get_response(request)
        except Exception as error:
            buffer_backend_session_log(
                session_id=session_id,
                level="error",
                event="backend.request.exception",
                message=str(error),
                request=request,
                metadata={"error_type": type(error).__name__},
            )
            raise

        duration_ms = int((time.monotonic() - started_at) * 1000)

        if session_id and request.path.startswith("/api/"):
            level = "info"
            if(response.status_code >= 500):
                level = "error"
            elif(response.status_code >= 400):
                level = "warning"

            # level = "error" if response.status_code >= 500 else "warning" if response.status_code >= 400 else "info"

            if level != "info":
                buffer_backend_session_log(
                    session_id=session_id,
                    level=level,
                    event="backend.request",
                    message=f"{request.method} {request.path} -> {response.status_code}",
                    request=request,
                    status_code=response.status_code,
                    metadata={"duration_ms": duration_ms},
                )

        return response