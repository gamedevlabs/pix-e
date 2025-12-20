"""
SPARC V2 Streaming API views.

Provides real-time progress updates via Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
import os
import tempfile
import time
from typing import Any, Dict, Generator, List, Optional, cast

from django.conf import settings
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from llm.config import get_config
from llm.events import EventCollector
from llm.logfire_config import get_logfire
from llm.providers.manager import ModelManager
from llm.types import AgentOutputEvent, AgentStartedEvent
from sparc.llm.utils.file_extraction import validate_file_size, validate_file_type
from sparc.llm.views.v2 import VALID_PILLAR_MODES, get_model_id, save_game_concept
from sparc.llm.workflows_v2 import SPARCRouterWorkflow
from sparc.models import SPARCEvaluation

logger = logging.getLogger(__name__)


class ProgressEventCollector(EventCollector):
    """Event collector that yields progress updates for SSE."""

    def __init__(self) -> None:
        """Initialize with a queue for progress events."""
        super().__init__()
        self.progress_queue: List[Dict[str, Any]] = []

    def add_agent_started(self, agent_name: str) -> AgentStartedEvent:
        """Track agent start and emit progress."""
        event = super().add_agent_started(agent_name)
        self.progress_queue.append(
            {"type": "agent_started", "agent": agent_name, "timestamp": time.time()}
        )
        return event

    def add_agent_finished(self, agent_name: str) -> AgentOutputEvent:
        """Track agent finish and emit progress."""
        event = super().add_agent_finished(agent_name)
        self.progress_queue.append(
            {"type": "agent_finished", "agent": agent_name, "timestamp": time.time()}
        )
        return event

    def get_progress_events(self) -> List[Dict[str, Any]]:
        """Get all queued progress events and clear queue."""
        events = self.progress_queue.copy()
        self.progress_queue.clear()
        return events


class SPARCV2StreamView(APIView):
    """
    V2 evaluation with real-time progress via SSE.

    POST /api/sparc/v2/evaluate-stream/
    Body: {
        "game_text": "...",
        "model": "gemini" | "openai" (optional)
    }

    Returns Server-Sent Events stream with progress updates.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> StreamingHttpResponse:
        """Execute V2 evaluation with streaming progress."""
        document_data = None
        temp_file_path = None

        try:
            game_text = request.data.get("game_text")
            if not game_text:
                return StreamingHttpResponse(
                    self._error_stream("Missing required field: 'game_text'"),
                    content_type="text/event-stream",
                    status=400,
                )

            model_name = request.data.get("model", "openai")
            model_id = get_model_id(model_name)
            context_text = request.data.get("context", "")
            pillar_mode = request.data.get("pillar_mode", "smart")
            context_strategy = request.data.get("context_strategy")
            if pillar_mode not in VALID_PILLAR_MODES:
                return StreamingHttpResponse(
                    self._error_stream("Invalid pillar_mode"),
                    content_type="text/event-stream",
                    status=400,
                )

            # Handle optional document upload
            uploaded_file = request.FILES.get("document")
            logger.info(f"[UPLOAD CHECK] uploaded_file: {uploaded_file}")
            if uploaded_file:
                logger.info(f"[UPLOAD] Processing file: {uploaded_file.name}")
                try:
                    # Validate file type
                    file_type = validate_file_type(
                        uploaded_file.name, settings.ALLOWED_DOCUMENT_TYPES
                    )

                    # Validate file size
                    validate_file_size(
                        uploaded_file.size, settings.DOCUMENT_MAX_SIZE_MB
                    )

                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{file_type}", dir=tempfile.gettempdir()
                    ) as tmp_file:
                        for chunk in uploaded_file.chunks():
                            tmp_file.write(chunk)
                        temp_file_path = tmp_file.name

                    document_data = {
                        "file_path": temp_file_path,
                        "file_type": file_type,
                        "original_name": uploaded_file.name,
                    }

                except ValueError as e:
                    logger.error(f"File validation failed: {e}")
                    return StreamingHttpResponse(
                        self._error_stream(f"File validation failed: {str(e)}"),
                        content_type="text/event-stream",
                        status=400,
                    )
                except Exception as e:
                    logger.error(f"File upload failed: {e}", exc_info=True)
                    return StreamingHttpResponse(
                        self._error_stream(f"File upload failed: {str(e)}"),
                        content_type="text/event-stream",
                        status=500,
                    )

            # Create evaluation record
            evaluation = SPARCEvaluation.objects.create(
                game_text=game_text,
                context=context_text,
                mode="router_v2",
                pillar_mode=pillar_mode,
                model_id=model_id,
                execution_time_ms=0,
                total_tokens=0,
                estimated_cost_eur=0,
            )

            # Stream the evaluation with progress
            return StreamingHttpResponse(
                self._stream_evaluation(
                    game_text,
                    context_text,
                    pillar_mode,
                    context_strategy,
                    model_id,
                    evaluation,
                    cast(User, request.user),
                    document_data,
                    temp_file_path,
                ),
                content_type="text/event-stream",
            )

        except Exception as e:
            logger.error(f"Evaluation failed: {e}", exc_info=True)
            # Clean up temp file on error
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file: {cleanup_error}")
            return StreamingHttpResponse(
                self._error_stream(str(e)),
                content_type="text/event-stream",
                status=500,
            )

    def _stream_evaluation(
        self,
        game_text: str,
        context_text: str,
        pillar_mode: str,
        context_strategy: Optional[str],
        model_id: str,
        evaluation: SPARCEvaluation,
        user: User,
        document_data: Optional[Dict[str, Any]] = None,
        temp_file_path: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Stream evaluation progress and results."""
        logfire = get_logfire()

        # Create top-level span for the entire evaluation
        with logfire.span(
            "sparc.v2.evaluate_stream",
            model=model_id,
            pillar_mode=pillar_mode,
            game_text_length=len(game_text),
        ):
            config = get_config()
            model_manager = ModelManager(config)
            event_collector = ProgressEventCollector()

            workflow = SPARCRouterWorkflow(
                model_manager=model_manager,
                config=config,
                event_collector=event_collector,
                evaluation=evaluation,
                user=user if user.is_authenticated else None,
            )

            from llm.types import LLMRequest

            request_data: Dict[str, Any] = {
                "game_text": game_text,
                "context": context_text,
                "pillar_mode": pillar_mode,
            }
            if context_strategy:
                request_data["context_strategy"] = context_strategy

            # Add document data if provided
            if document_data:
                request_data["document_file"] = document_data
                logger.info(
                    f"Document upload detected: {document_data['original_name']} "
                    f"({document_data['file_type']})"
                )
            else:
                logger.info("No document uploaded for this evaluation")

            request = LLMRequest(
                feature="sparc",
                operation="router_v2",
                data=request_data,
                model_id=model_id,
                mode="agentic",
            )

            # Debug: Log document file status
            doc_status = "WITH DOCUMENT" if document_data else "NO DOCUMENT"
            logger.info(f"[SPARC V2] Starting evaluation {doc_status}")

            # Send initial progress
            yield self._format_sse(
                "progress",
                {"stage": "starting", "message": "Initializing evaluation..."},
            )

            # Run the workflow asynchronously and stream progress
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Track progress
                aspect_count = 0
                total_aspects = 10

                # Start the evaluation
                task = loop.create_task(workflow.run(request, mode="full"))

                # Poll for progress updates
                while not task.done():
                    # Check for new progress events
                    events = event_collector.get_progress_events()
                    for event in events:
                        if event["type"] == "agent_finished":
                            agent_name = event["agent"]

                            if agent_name == "router":
                                yield self._format_sse(
                                    "progress",
                                    {
                                        "stage": "router_complete",
                                        "message": "Content extraction complete",
                                    },
                                )
                            elif agent_name == "synthesis":
                                yield self._format_sse(
                                    "progress",
                                    {
                                        "stage": "synthesis_complete",
                                        "message": "Synthesis complete",
                                    },
                                )
                            elif agent_name.endswith("_v2"):
                                aspect_count += 1
                                yield self._format_sse(
                                    "progress",
                                    {
                                        "stage": "aspects_progress",
                                        "message": f"Aspect evaluation: {aspect_count}/{total_aspects}",  # noqa: E501
                                        "current": aspect_count,
                                        "total": total_aspects,
                                    },
                                )

                    # Small delay to avoid busy waiting
                    loop.run_until_complete(asyncio.sleep(0.1))

                # Get the result
                result = task.result()

                if not result.success:
                    yield self._format_sse(
                        "error",
                        {
                            "message": "Evaluation failed",
                            "errors": [e.message for e in result.errors],
                        },
                    )
                    return

                # Update evaluation record
                aggregated = result.aggregated_data
                evaluation.execution_time_ms = aggregated.get(
                    "execution_time_ms", 0
                )  # noqa: E501
                evaluation.total_tokens = aggregated.get("total_tokens", 0)
                evaluation.estimated_cost_eur = aggregated.get(
                    "estimated_cost_eur", 0
                )  # noqa: E501
                evaluation.save()

                # Auto-save game concept
                save_game_concept(user, game_text, evaluation)

                # Send final result
                yield self._format_sse("complete", aggregated)

            except Exception as e:
                logger.exception(f"Error in SPARC V2 streaming evaluation: {e}")
                yield self._format_sse("error", {"message": str(e)})

            finally:
                # Clean up temporary file after workflow execution completes
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temp file: {cleanup_error}")
                loop.close()

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def _error_stream(self, message: str) -> Generator[str, None, None]:
        """Generate error SSE stream."""
        yield self._format_sse("error", {"message": message})
