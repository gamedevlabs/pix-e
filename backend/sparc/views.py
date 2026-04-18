"""
SPARC API views.

Provides endpoints for both agentic (quick scan) and monolithic
SPARC evaluations.
"""

import logging
from typing import Any, Callable, Optional

from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.views import APIView

from backend.llm import LLMOrchestrator
from backend.llm.logfire_config import get_logfire
from backend.llm.types import LLMRequest, LLMResponse
from backend.llm.view_utils import get_model_id
from game_concept.models import Project
from game_concept.utils import get_current_project

# Import handlers and workflows to trigger auto-registration
from sparc.llm import handlers, workflows  # noqa: F401
from sparc.llm.views.v2_utils import resolve_concept_meta
from sparc.models import SPARCEvaluation, SPARCEvaluationResult
from sparc.serializers import SPARCEvaluationSerializer

logger = logging.getLogger(__name__)
ASPECT_MAPPING = {
    "player_experience": "player_experience",
    "theme": "theme",
    "gameplay": "gameplay",
    "place": "place",
    "unique_features": "unique_features",
    "story_narrative": "story_narrative",
    "goals_challenges_rewards": "goals_challenges_rewards",
    "art_direction": "art_direction",
    "purpose": "purpose",
    "opportunities_risks": "opportunities_risks",
}


def save_sparc_evaluation(
    game_text: str, context: str, mode: str, response: LLMResponse
) -> SPARCEvaluation:
    """
    Save SPARC evaluation and its aspect results to database.

    Args:
        game_text: The game concept text
        context: Additional context provided
        mode: Execution mode (quick_scan, monolithic, etc.)
        response: LLMResponse from orchestrator

    Returns:
        The created SPARCEvaluation instance
    """
    # Extract metadata
    metadata = response.metadata
    token_usage = metadata.token_usage if metadata.token_usage else None

    # Get model name (cost tracking disabled)
    model_name = metadata.models_used[0].name if metadata.models_used else "unknown"

    prompt_tokens = token_usage.prompt_tokens if token_usage else 0
    completion_tokens = token_usage.completion_tokens if token_usage else 0
    cost_eur = 0

    # Create evaluation record
    evaluation = SPARCEvaluation.objects.create(
        game_text=game_text,
        context=context,
        mode=mode,
        model_id=model_name,
        execution_time_ms=metadata.execution_time_ms,
        total_tokens=token_usage.total_tokens if token_usage else 0,
        estimated_cost_eur=cost_eur,
    )

    # For quick_scan (agentic), save individual aspect results
    if mode == "quick_scan" and metadata.agents_used:
        for agent in metadata.agents_used:
            aspect_key = agent.name
            if aspect_key in ASPECT_MAPPING and aspect_key in response.results:
                aspect_data = response.results[aspect_key]
                score = (
                    aspect_data.get("score") if isinstance(aspect_data, dict) else None
                )

                agent_cost = 0

                SPARCEvaluationResult.objects.create(
                    evaluation=evaluation,
                    aspect=ASPECT_MAPPING[aspect_key],
                    score=score,
                    agent_name=agent.name,
                    model_used=agent.model,
                    execution_time_ms=agent.execution_time_ms,
                    prompt_tokens=agent.prompt_tokens,
                    completion_tokens=agent.completion_tokens,
                    total_tokens=agent.total_tokens,
                    estimated_cost_eur=agent_cost,
                    result_data=aspect_data,
                )

        # Also save the full aggregated response with token totals
        SPARCEvaluationResult.objects.create(
            evaluation=evaluation,
            aspect="aggregated",
            score=response.results.get("readiness_score"),
            agent_name="aggregator",
            model_used=model_name,
            execution_time_ms=metadata.execution_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_eur=cost_eur,
            result_data=response.results,
        )

    # For monolithic, save as a single aggregated result
    elif mode == "monolithic":
        model_used = metadata.models_used[0].name if metadata.models_used else "unknown"
        SPARCEvaluationResult.objects.create(
            evaluation=evaluation,
            aspect="player_experience",  # Use first aspect as placeholder
            score=None,
            agent_name="monolithic",
            model_used=model_used,
            execution_time_ms=metadata.execution_time_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_eur=cost_eur,
            result_data=response.results,
        )

    return evaluation


def save_game_concept(
    user: User, game_text: str, evaluation: Optional[SPARCEvaluation] = None
) -> None:
    """
    Auto-save game concept after SPARC evaluation.

    Args:
        user: The authenticated user
        game_text: The game concept text to save
        evaluation: Optional SPARCEvaluation to link to this concept
    """
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

    # Mark all existing concepts as not current
    project.game_concepts.filter(is_current=True).update(is_current=False)

    # Create new current concept with linked evaluation
    project.game_concepts.create(
        user=user,
        content=game_text,
        is_current=True,
        last_sparc_evaluation=evaluation,
    )


def _build_llm_request(
    *,
    operation: str,
    game_text: str,
    model_id: str,
    mode: Optional[str] = None,
    extra_data: Optional[dict[str, Any]] = None,
) -> LLMRequest:
    data = {"game_text": game_text}
    if extra_data:
        data.update(extra_data)
    return LLMRequest(
        feature="sparc",
        operation=operation,
        data=data,
        model_id=model_id,
        mode=mode,
    )


def _run_sparc_evaluation(
    *,
    request: Request,
    orchestrator: LLMOrchestrator,
    operation: str,
    mode: str,
    span_name: str,
    execution_mode: str,
    strategy: str,
    extra_data: Optional[dict[str, Any]] = None,
    log_event: Optional[str] = None,
    log_payload: Optional[Callable[[LLMResponse], dict[str, Any]]] = None,
    error_event: str = "sparc.evaluation.error",
) -> JsonResponse:
    logfire = get_logfire()
    concept_meta = resolve_concept_meta(request)
    with logfire.span(
        "sparc.evaluate.concept",
        feature="sparc",
        mode=mode,
        **concept_meta,
    ):
        with logfire.span(
            span_name,
            feature="sparc",
            strategy=strategy,
            execution_mode=execution_mode,
            model=request.data.get("model", "openai"),
            game_text_length=len(request.data.get("game_text", "")),
        ):
            try:
                game_text = request.data.get("game_text")
                if not game_text:
                    return JsonResponse(
                        {"error": "Missing required field: 'game_text'"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                model_name = request.data.get("model", "openai")
                model_id = get_model_id(model_name)

                llm_request = _build_llm_request(
                    operation=operation,
                    game_text=game_text,
                    model_id=model_id,
                    mode=execution_mode if execution_mode == "agentic" else None,
                    extra_data=extra_data,
                )

                response = orchestrator.execute(llm_request)

                if not response.success:
                    error_messages = [err.message for err in response.errors]
                    return JsonResponse(
                        {"error": "Evaluation failed", "details": error_messages},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                if log_event and log_payload:
                    logfire.info(log_event, **log_payload(response))

                context = request.data.get("context", "")
                evaluation = save_sparc_evaluation(game_text, context, mode, response)

                if request.user.is_authenticated:
                    user: User = request.user  # type: ignore[assignment]
                    save_game_concept(user, game_text, evaluation)

                return JsonResponse(response.results, status=status.HTTP_200_OK)

            except Exception as e:
                logfire.exception(error_event, error=str(e))
                logger.exception("Error in SPARC evaluation: %s", e)
                return JsonResponse(
                    {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class SPARCQuickScanView(APIView):
    """
    Quick scan evaluation using parallel agentic execution.

    Runs all 10 SPARC agents in parallel for comprehensive evaluation.

    POST /api/sparc/quick-scan/
    Body: {
        "game_text": "...",
        "model": "gemini" | "openai" (optional, defaults to "openai")
    }

    Response: {
        "readiness_score": 0-100,
        "readiness_status": "Ready" | "Nearly Ready" | "Needs Work" |
                           "Not Ready",
        "aspect_scores": [...],
        "strongest_aspects": [...],
        "weakest_aspects": [...],
        "critical_gaps": [...],
        "estimated_time_to_ready": "...",
        "next_steps": [...],
        "player_experience": {...},
        "theme": {...},
        ... (all 10 aspect results)
    }
    """

    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.orchestrator = LLMOrchestrator()

    def post(self, request: Request) -> JsonResponse:
        """Execute quick scan evaluation with agentic execution."""
        context_strategy = request.data.get("context_strategy", "default")
        extra_data = {}
        if request.data.get("context_strategy"):
            extra_data["context_strategy"] = request.data.get("context_strategy")

        return _run_sparc_evaluation(
            request=request,
            orchestrator=self.orchestrator,
            operation="quick_scan",
            mode="quick_scan",
            span_name=f"sparc.evaluate.quick_scan.{context_strategy}.agentic",
            execution_mode="agentic",
            strategy=context_strategy,
            extra_data=extra_data or None,
            log_event="sparc.quick_scan.completed",
            log_payload=lambda response: {
                "readiness_score": response.results.get("readiness_score"),
                "execution_time_ms": response.metadata.execution_time_ms,
                "total_tokens": (
                    response.metadata.token_usage.total_tokens
                    if response.metadata.token_usage
                    else 0
                ),
                "num_agents": (
                    len(response.metadata.agents_used)
                    if response.metadata.agents_used
                    else 0
                ),
            },
            error_event="sparc.quick_scan.error",
        )


class SPARCMonolithicView(APIView):
    """
    Monolithic baseline evaluation for comparison.

    Uses original single-shot SPARC prompt for baseline comparison
    against the agentic approach.

    POST /api/sparc/monolithic/
    Body: {
        "game_text": "...",
        "model": "gemini" | "openai" (optional, defaults to "openai")
    }

    Response: {
        "overall_assessment": "...",
        "aspects_evaluated": {...},
        "missing_aspects": [...],
        "suggestions": [...],
        "additional_details": [...],
        "readiness_verdict": "..."
    }
    """

    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.orchestrator = LLMOrchestrator()

    def post(self, request: Request) -> JsonResponse:
        """Execute monolithic evaluation with handler-based execution."""
        return _run_sparc_evaluation(
            request=request,
            orchestrator=self.orchestrator,
            operation="monolithic",
            mode="monolithic",
            span_name="sparc.evaluate.monolithic.default.monolithic",
            execution_mode="monolithic",
            strategy="default",
            log_event="sparc.monolithic.completed",
            log_payload=lambda response: {
                "execution_time_ms": response.metadata.execution_time_ms,
                "total_tokens": (
                    response.metadata.token_usage.total_tokens
                    if response.metadata.token_usage
                    else 0
                ),
            },
            error_event="sparc.monolithic.error",
        )


class SPARCEvaluationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving SPARC evaluations.

    Endpoints:
    - GET /api/sparc/evaluations/ - List all evaluations
    - GET /api/sparc/evaluations/{id}/ - Get specific evaluation

    Read-only access to evaluation history.
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = SPARCEvaluationSerializer
    queryset = SPARCEvaluation.objects.all().order_by("-created_at")
