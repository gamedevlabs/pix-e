"""
SPARC V2 Streaming API views.

Provides real-time progress updates via Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Generator, List, Optional, cast

from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from llm.events import EventCollector
from llm.logfire_config import get_logfire
from llm.types import AgentOutputEvent, AgentStartedEvent
from sparc.llm.views.v2 import save_game_concept
from sparc.llm.views.v2_utils import (
    VALID_PILLAR_MODES,
    build_request_data,
    create_evaluation,
    get_model_id,
    resolve_concept_meta,
    run_router_workflow,
    save_uploaded_document,
    update_evaluation_totals,
)
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
            logger.info("[UPLOAD CHECK] uploaded_file: %s", uploaded_file)
            if uploaded_file:
                logger.info("[UPLOAD] Processing file: %s", uploaded_file.name)
                try:
                    document_data, temp_file_path = save_uploaded_document(
                        uploaded_file
                    )
                except ValueError as e:
                    logger.error("File validation failed: %s", e)
                    return StreamingHttpResponse(
                        self._error_stream(f"File validation failed: {str(e)}"),
                        content_type="text/event-stream",
                        status=400,
                    )
                except Exception as e:
                    logger.error("File upload failed: %s", e, exc_info=True)
                    return StreamingHttpResponse(
                        self._error_stream(f"File upload failed: {str(e)}"),
                        content_type="text/event-stream",
                        status=500,
                    )

            evaluation = create_evaluation(
                game_text=game_text,
                context_text=context_text,
                mode="router_v2",
                pillar_mode=pillar_mode,
                model_id=model_id,
            )

            # Stream the evaluation with progress
            concept_meta = resolve_concept_meta(request)
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
                    concept_meta,
                    request.data.get("project_id"),
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
        concept_meta: Optional[Dict[str, str]] = None,
        project_id: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """Stream evaluation progress and results."""
        logfire = get_logfire()

        # Create top-level span for the entire evaluation
        with logfire.span(
            "sparc.evaluate.concept",
            feature="sparc",
            mode="router_v2",
            **(concept_meta or {}),
        ):
            with logfire.span(
                "sparc.evaluate.router_v2.agentic",
                model=model_id,
                pillar_mode=pillar_mode,
                game_text_length=len(game_text),
            ):
                event_collector = ProgressEventCollector()
                request_data = build_request_data(
                    game_text=game_text,
                    context_text=context_text,
                    pillar_mode=pillar_mode,
                    project_id=project_id,
                    context_strategy=context_strategy,
                    document_data=document_data,
                )
                if document_data:
                    logger.info(
                        "Document upload detected: %s (%s)",
                        document_data["original_name"],
                        document_data["file_type"],
                    )
                else:
                    logger.info("No document uploaded for this evaluation")

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
                    task = loop.create_task(
                        asyncio.to_thread(
                            run_router_workflow,
                            request_data=request_data,
                            model_id=model_id,
                            evaluation=evaluation,
                            user=user if user.is_authenticated else None,
                            mode="full",
                            event_collector=event_collector,
                        )
                    )

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

                    aggregated = result.aggregated_data
                    update_evaluation_totals(evaluation, aggregated)

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
                            logger.warning(
                                f"Failed to clean up temp file: {cleanup_error}"
                            )
                    loop.close()

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def _error_stream(self, message: str) -> Generator[str, None, None]:
        """Generate error SSE stream."""
        yield self._format_sse("error", {"message": message})
