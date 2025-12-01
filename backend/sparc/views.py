"""
SPARC API views.

Provides endpoints for both agentic (quick scan) and monolithic
SPARC evaluations.
"""

import logging

from django.http import JsonResponse
from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView

from backend.llm import LLMOrchestrator
from backend.llm.cost_tracking import calculate_cost_eur
from backend.llm.types import LLMRequest, LLMResponse
from backend.llm.view_utils import get_model_id
from game_concept.models import GameConcept

# Import handlers and graphs to trigger auto-registration
from sparc.llm import graphs, handlers  # noqa: F401
from sparc.models import SPARCEvaluation, SPARCEvaluationResult
from sparc.serializers import SPARCEvaluationSerializer

logger = logging.getLogger(__name__)


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

    # Get model name and calculate cost
    model_name = metadata.models_used[0].name if metadata.models_used else "unknown"

    # Calculate cost based on actual token usage
    prompt_tokens = token_usage.prompt_tokens if token_usage else 0
    completion_tokens = token_usage.completion_tokens if token_usage else 0
    cost_eur = calculate_cost_eur(model_name, prompt_tokens, completion_tokens)

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
        aspect_mapping = {
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

        for agent in metadata.agents_used:
            aspect_key = agent.name
            if aspect_key in aspect_mapping and aspect_key in response.results:
                aspect_data = response.results[aspect_key]
                score = (
                    aspect_data.get("score") if isinstance(aspect_data, dict) else None
                )

                # Calculate per-agent cost
                agent_cost = calculate_cost_eur(
                    agent.model, agent.prompt_tokens, agent.completion_tokens
                )

                SPARCEvaluationResult.objects.create(
                    evaluation=evaluation,
                    aspect=aspect_mapping[aspect_key],
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


def save_game_concept(user, game_text: str, evaluation=None) -> None:
    """
    Auto-save game concept after SPARC evaluation.

    Args:
        user: The authenticated user
        game_text: The game concept text to save
        evaluation: Optional SPARCEvaluation to link to this concept
    """
    if not user.is_authenticated:
        return

    # Mark all existing concepts as not current
    GameConcept.objects.filter(user=user, is_current=True).update(is_current=False)

    # Create new current concept with linked evaluation
    GameConcept.objects.create(
        user=user,
        content=game_text,
        is_current=True,
        last_sparc_evaluation=evaluation,
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = LLMOrchestrator()

    def post(self, request):
        """Execute quick scan evaluation with agentic execution."""
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

            # Create orchestrator request for agentic execution
            llm_request = LLMRequest(
                feature="sparc",
                operation="quick_scan",
                data={"game_text": game_text},
                model_id=model_id,
                mode="agentic",  # Use agentic mode for graph execution
            )

            # Execute through orchestrator (will use agent graph)
            response = self.orchestrator.execute(llm_request)

            if not response.success:
                error_messages = [err.message for err in response.errors]
                return JsonResponse(
                    {"error": "Evaluation failed", "details": error_messages},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save evaluation to database
            context = request.data.get("context", "")
            evaluation = save_sparc_evaluation(
                game_text, context, "quick_scan", response
            )

            # Auto-save game concept with linked evaluation
            save_game_concept(request.user, game_text, evaluation)

            return JsonResponse(response.results, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error in SPARC evaluation: {e}")
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orchestrator = LLMOrchestrator()

    def post(self, request):
        """Execute monolithic evaluation with handler-based execution."""
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

            # Create orchestrator request for monolithic execution
            llm_request = LLMRequest(
                feature="sparc",
                operation="monolithic",
                data={"game_text": game_text},
                model_id=model_id,
            )

            # Execute through orchestrator (will use handler)
            response = self.orchestrator.execute(llm_request)

            if not response.success:
                error_messages = [err.message for err in response.errors]
                return JsonResponse(
                    {"error": "Evaluation failed", "details": error_messages},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save evaluation to database
            context = request.data.get("context", "")
            evaluation = save_sparc_evaluation(
                game_text, context, "monolithic", response
            )

            # Auto-save game concept with linked evaluation
            save_game_concept(request.user, game_text, evaluation)

            return JsonResponse(response.results, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f"Error in SPARC evaluation: {e}")
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
