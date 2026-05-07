"""
SPARC V2 API views.

Router-based agentic evaluation endpoints.
"""

import logging
import os
from typing import Optional, cast

from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.views import APIView

from game_concept.models import Project
from game_concept.utils import get_current_project
from llm.logfire_config import get_logfire

# Import to trigger workflow registration
from sparc.llm import workflows, workflows_v2  # noqa: F401
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
        concept_meta = resolve_concept_meta(request)
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
                            document_data, temp_file_path = save_uploaded_document(
                                uploaded_file
                            )

                            logger.info(
                                "Document uploaded: %s (%s bytes, type: %s)",
                                uploaded_file.name,
                                uploaded_file.size,
                                document_data["file_type"],
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

                    evaluation = create_evaluation(
                        game_text=game_text,
                        context_text=context_text,
                        mode="router_v2",
                        pillar_mode=pillar_mode,
                        model_id=model_id,
                    )

                    request_data = build_request_data(
                        game_text=game_text,
                        context_text=context_text,
                        pillar_mode=pillar_mode,
                        project_id=request.data.get("project_id"),
                        context_strategy=context_strategy,
                        document_data=document_data,
                    )
                    result = run_router_workflow(
                        request_data=request_data,
                        model_id=model_id,
                        evaluation=evaluation,
                        user=request.user if request.user.is_authenticated else None,
                        mode="full",
                    )

                    if not result.success:
                        return JsonResponse(
                            {
                                "error": "Evaluation failed",
                                "details": [e.message for e in result.errors],
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    aggregated = result.aggregated_data
                    update_evaluation_totals(evaluation, aggregated)

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
        concept_meta = resolve_concept_meta(request)
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

                    evaluation = create_evaluation(
                        game_text=game_text,
                        context_text=context_text,
                        mode=f"router_v2_{mode}",
                        pillar_mode=pillar_mode,
                        model_id=model_id,
                    )

                    request_data = build_request_data(
                        game_text=game_text,
                        context_text=context_text,
                        pillar_mode=pillar_mode,
                        project_id=request.data.get("project_id"),
                        context_strategy=context_strategy,
                    )
                    result = run_router_workflow(
                        request_data=request_data,
                        model_id=model_id,
                        evaluation=evaluation,
                        user=request.user if request.user.is_authenticated else None,
                        mode=mode,
                        target_aspects=target_aspects,
                    )

                    if not result.success:
                        return JsonResponse(
                            {
                                "error": "Evaluation failed",
                                "details": [e.message for e in result.errors],
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

                    aggregated = result.aggregated_data
                    update_evaluation_totals(evaluation, aggregated)

                    return JsonResponse(aggregated, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.exception(f"Error in SPARC V2 evaluation: {e}")
                    return JsonResponse(
                        {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
