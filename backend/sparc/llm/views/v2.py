"""
SPARC V2 API views.

Router-based agentic evaluation endpoints.
"""

import asyncio
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, cast

from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from game_concept.models import Project
from game_concept.utils import get_current_game_concept, get_current_project
from llm.config import get_config
from llm.events import EventCollector
from llm.logfire_config import get_logfire
from llm.providers.manager import ModelManager

# Import to trigger workflow registration
from sparc.llm import workflows, workflows_v2  # noqa: F401
from sparc.llm.utils.file_extraction import validate_file_size, validate_file_type
from sparc.llm.workflows_v2 import SPARCRouterWorkflow
from sparc.models import SPARCEvaluation

logger = logging.getLogger(__name__)

VALID_PILLAR_MODES = {"all", "smart", "none"}


def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs using config."""
    config = get_config()
    return config.resolve_model_alias(model_name)


def _resolve_concept_meta(request: Request) -> dict[str, str]:
    project = None
    project_id = request.data.get("project_id")
    if project_id:
        project = Project.objects.filter(id=project_id).first()
    elif request.user.is_authenticated:
        project = get_current_project(request.user)
    concept = get_current_game_concept(project) if project else None
    concept_text = (concept.content or "") if concept else ""
    preview = (
        concept_text[:80] + "..."
        if concept_text and len(concept_text) > 80
        else concept_text
    )
    return {
        "project_id": str(getattr(project, "id", "")) if project else "",
        "project_name": getattr(project, "name", "") if project else "",
        "concept_name": getattr(project, "name", "") if project else "",
        "concept_preview": preview,
    }


def save_game_concept(
    user: User, game_text: str, evaluation: Optional[SPARCEvaluation] = None
) -> None:
    """Auto-save game concept after SPARC evaluation."""
    if not user.is_authenticated:
        return

    project = get_current_project(user)
    if not project:
        project = Project.objects.create(user=user, name="Untitled Project")

    current = project.game_concepts.filter(is_current=True).first()
    if current and current.content == game_text:
        if evaluation:
            current.last_sparc_evaluation = evaluation
            current.save(update_fields=["last_sparc_evaluation", "updated_at"])
        return

    project.game_concepts.filter(is_current=True).update(is_current=False)
    project.game_concepts.create(
        user=user,
        content=game_text,
        is_current=True,
        last_sparc_evaluation=evaluation,
    )


class SPARCV2EvaluateView(APIView):
    """
    V2 full evaluation using router-based agentic execution.

    Runs: Router → 10 parallel aspect agents → Synthesis

    POST /api/sparc/v2/evaluate/
    Body: {
        "game_text": "...",
        "model": "gemini" | "openai" (optional, defaults to "openai")
    }

    Response: {
        "aspect_results": {
            "player_experience": {...},
            "theme": {...},
            ...
        },
        "synthesis": {
            "overall_status": "ready" | "nearly_ready" | "needs_work",
            "overall_reasoning": "...",
            "strongest_aspects": [...],
            "weakest_aspects": [...],
            "critical_gaps": [...],
            "next_steps": [...]
        },
        "mode": "full",
        "model_id": "...",
        "execution_time_ms": 1234,
        "total_tokens": 5678,
        "estimated_cost_eur": 0.001234
    }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> JsonResponse:
        """Execute full V2 evaluation."""
        logfire = get_logfire()
        concept_meta = _resolve_concept_meta(request)
        temp_file_path = None  # Track temp file for cleanup
        with logfire.span(
            "sparc.evaluate.concept",
            feature="sparc",
            mode="router_v2",
            **concept_meta,
        ):
            with logfire.span(
                "sparc.evaluate.router_v2.agentic",
                feature="sparc",
                execution_mode="agentic",
                model=request.data.get("model", "openai"),
                game_text_length=len(request.data.get("game_text", "")),
            ):
                try:
                    # Validate input
                    game_text = request.data.get("game_text")
                    if not game_text:
                        return JsonResponse(
                            {"error": "Missing required field: 'game_text'"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Get model preference
                    model_name = request.data.get("model", "openai")
                    model_id = get_model_id(model_name)

                    # Resolve optional inputs
                    context_text = request.data.get("context", "")
                    pillar_mode = request.data.get("pillar_mode", "smart")
                    context_strategy = request.data.get("context_strategy")
                    if pillar_mode not in VALID_PILLAR_MODES:
                        return JsonResponse(
                            {"error": "Invalid pillar_mode"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Handle optional document upload
                    document_data = None
                    uploaded_file = request.FILES.get("document")

                    if uploaded_file:
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
                                delete=False,
                                suffix=f".{file_type}",
                                dir=tempfile.gettempdir(),
                            ) as tmp_file:
                                for chunk in uploaded_file.chunks():
                                    tmp_file.write(chunk)
                                temp_file_path = tmp_file.name

                            document_data = {
                                "file_path": temp_file_path,
                                "file_type": file_type,
                                "original_name": uploaded_file.name,
                            }

                            logger.info(
                                f"Document uploaded: {uploaded_file.name} "
                                f"({uploaded_file.size} bytes, type: {file_type})"
                            )

                        except ValueError as e:
                            return JsonResponse(
                                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
                            )
                        except Exception as e:
                            logger.error(f"File upload failed: {str(e)}")
                            return JsonResponse(
                                {"error": f"File upload failed: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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

                    # Execute workflow
                    result = self._execute_workflow(
                        game_text=game_text,
                        context_text=context_text,
                        model_id=model_id,
                        mode="full",
                        evaluation=evaluation,
                        pillar_mode=pillar_mode,
                        context_strategy=context_strategy,
                        user=request.user if request.user.is_authenticated else None,
                        project_id=request.data.get("project_id"),
                        document_data=document_data,
                    )

                    if not result["success"]:
                        return JsonResponse(
                            {
                                "error": "Evaluation failed",
                                "details": result.get("errors", []),
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    # Update evaluation with totals
                    aggregated = result["aggregated_data"]
                    evaluation.execution_time_ms = aggregated.get(
                        "execution_time_ms", 0
                    )
                    evaluation.total_tokens = aggregated.get("total_tokens", 0)
                    evaluation.estimated_cost_eur = aggregated.get(
                        "estimated_cost_eur", 0
                    )
                    evaluation.save()

                    # Auto-save game concept
                    if request.user.is_authenticated:
                        save_game_concept(
                            cast(User, request.user), game_text, evaluation
                        )

                    return JsonResponse(aggregated, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.exception(f"Error in SPARC V2 evaluation: {e}")
                    return JsonResponse(
                        {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                finally:
                    # Clean up temporary file
                    if temp_file_path:
                        try:
                            os.unlink(temp_file_path)
                            logger.debug(f"Cleaned up temp file: {temp_file_path}")
                        except Exception as e:
                            logger.warning(f"Failed to clean up temp file: {str(e)}")

    def _execute_workflow(
        self,
        game_text: str,
        context_text: str,
        model_id: str,
        mode: str,
        evaluation: SPARCEvaluation,
        pillar_mode: str,
        context_strategy: Optional[str],
        user: Optional[User],
        project_id: Optional[int] = None,
        target_aspects: Optional[List[str]] = None,
        document_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the V2 workflow."""
        from llm.types import LLMRequest

        config = get_config()
        model_manager = ModelManager(config)
        event_collector = EventCollector()

        workflow = SPARCRouterWorkflow(
            model_manager=model_manager,
            config=config,
            event_collector=event_collector,
            evaluation=evaluation,
            user=user,
        )

        # Build request data
        request_data: Dict[str, Any] = {
            "game_text": game_text,
            "context": context_text,
            "pillar_mode": pillar_mode,
        }
        if project_id:
            request_data["project_id"] = project_id
        if context_strategy:
            request_data["context_strategy"] = context_strategy

        # Add document data if provided
        if document_data:
            request_data["document_file"] = document_data

        request = LLMRequest(
            feature="sparc",
            operation="router_v2",
            data=request_data,
            model_id=model_id,
            mode="agentic",
        )

        # Run async workflow in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                workflow.run(request, mode=mode, target_aspects=target_aspects)
            )
        finally:
            loop.close()

        return {
            "success": result.success,
            "aggregated_data": result.aggregated_data,
            "errors": [e.message for e in result.errors] if result.errors else [],
        }


class SPARCV2AspectView(APIView):
    """
    V2 single or multiple aspect evaluation.

    Runs: Router (focused) → Selected aspect agent(s)

    POST /api/sparc/v2/evaluate/aspect/
    Body: {
        "game_text": "...",
        "aspect": "art_direction",  # Single aspect
        "model": "gemini" | "openai" (optional)
    }

    OR

    POST /api/sparc/v2/evaluate/aspects/
    Body: {
        "game_text": "...",
        "aspects": ["gameplay", "art_direction"],  # Multiple aspects
        "model": "gemini" | "openai" (optional)
    }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> JsonResponse:
        """Execute single or multiple aspect evaluation."""
        logfire = get_logfire()
        concept_meta = _resolve_concept_meta(request)
        with logfire.span(
            "sparc.evaluate.concept",
            feature="sparc",
            mode="router_v2",
            **concept_meta,
        ):
            with logfire.span(
                "sparc.evaluate.router_v2.aspect.agentic",
                feature="sparc",
                execution_mode="agentic",
                model=request.data.get("model", "openai"),
                game_text_length=len(request.data.get("game_text", "")),
            ):
                try:
                    # Validate input
                    game_text = request.data.get("game_text")
                    if not game_text:
                        return JsonResponse(
                            {"error": "Missing required field: 'game_text'"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Resolve optional inputs
                    context_text = request.data.get("context", "")
                    pillar_mode = request.data.get("pillar_mode", "smart")
                    context_strategy = request.data.get("context_strategy")
                    if pillar_mode not in VALID_PILLAR_MODES:
                        return JsonResponse(
                            {"error": "Invalid pillar_mode"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Get target aspects
                    single_aspect = request.data.get("aspect")
                    multiple_aspects = request.data.get("aspects")

                    if single_aspect:
                        target_aspects = [single_aspect]
                        mode = "single"
                    elif multiple_aspects:
                        target_aspects = multiple_aspects
                        mode = "multiple"
                    else:
                        return JsonResponse(
                            {"error": "Missing 'aspect' or 'aspects' field"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    # Validate aspect names
                    valid_aspects = [
                        "player_experience",
                        "theme",
                        "purpose",
                        "gameplay",
                        "goals_challenges_rewards",
                        "place",
                        "story_narrative",
                        "unique_features",
                        "art_direction",
                        "opportunities_risks",
                    ]
                    for aspect in target_aspects:
                        if aspect not in valid_aspects:
                            return JsonResponse(
                                {"error": f"Invalid aspect: {aspect}"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                    # Get model preference
                    model_name = request.data.get("model", "openai")
                    model_id = get_model_id(model_name)

                    # Create evaluation record
                    evaluation = SPARCEvaluation.objects.create(
                        game_text=game_text,
                        context=context_text,
                        mode=f"router_v2_{mode}",
                        pillar_mode=pillar_mode,
                        model_id=model_id,
                        execution_time_ms=0,
                        total_tokens=0,
                        estimated_cost_eur=0,
                    )

                    # Execute workflow
                    result = self._execute_workflow(
                        game_text=game_text,
                        context_text=context_text,
                        model_id=model_id,
                        mode=mode,
                        evaluation=evaluation,
                        pillar_mode=pillar_mode,
                        context_strategy=context_strategy,
                        user=request.user if request.user.is_authenticated else None,
                        project_id=request.data.get("project_id"),
                        target_aspects=target_aspects,
                    )

                    if not result["success"]:
                        return JsonResponse(
                            {
                                "error": "Evaluation failed",
                                "details": result.get("errors", []),
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    # Update evaluation with totals
                    aggregated = result["aggregated_data"]
                    evaluation.execution_time_ms = aggregated.get(
                        "execution_time_ms", 0
                    )
                    evaluation.total_tokens = aggregated.get("total_tokens", 0)
                    evaluation.estimated_cost_eur = aggregated.get(
                        "estimated_cost_eur", 0
                    )
                    evaluation.save()

                    return JsonResponse(aggregated, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.exception(f"Error in SPARC V2 evaluation: {e}")
                    return JsonResponse(
                        {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

    def _execute_workflow(
        self,
        game_text: str,
        context_text: str,
        model_id: str,
        mode: str,
        evaluation: SPARCEvaluation,
        pillar_mode: str,
        context_strategy: Optional[str],
        user: Optional[User],
        project_id: Optional[int],
        target_aspects: List[str],
    ) -> Dict[str, Any]:
        """Execute the V2 workflow for specific aspects."""
        from llm.types import LLMRequest

        config = get_config()
        model_manager = ModelManager(config)
        event_collector = EventCollector()

        workflow = SPARCRouterWorkflow(
            model_manager=model_manager,
            config=config,
            event_collector=event_collector,
            evaluation=evaluation,
            user=user,
        )

        request_data: Dict[str, Any] = {
            "game_text": game_text,
            "context": context_text,
            "pillar_mode": pillar_mode,
        }
        if project_id:
            request_data["project_id"] = project_id
        if context_strategy:
            request_data["context_strategy"] = context_strategy

        request = LLMRequest(
            feature="sparc",
            operation="router_v2",
            data=request_data,
            model_id=model_id,
            mode="agentic",
        )

        # Run async workflow in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                workflow.run(request, mode=mode, target_aspects=target_aspects)
            )
        finally:
            loop.close()

        return {
            "success": result.success,
            "aggregated_data": result.aggregated_data,
            "errors": [e.message for e in result.errors] if result.errors else [],
        }
