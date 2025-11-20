"""
SPARC API views.

Provides endpoints for both agentic (quick scan) and monolithic SPARC evaluations.
"""

from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from backend.llm import LLMOrchestrator, get_config
from backend.llm.types import LLMRequest
from game_concept.models import GameConcept

# Import handlers and graphs to trigger auto-registration
from sparc.llm import graphs, handlers  # noqa: F401


def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs using orchestrator config."""
    config = get_config()
    return config.resolve_model_alias(model_name)


def save_game_concept(user, game_text: str) -> None:
    """
    Auto-save game concept after SPARC evaluation.

    Args:
        user: The authenticated user
        game_text: The game concept text to save
    """
    if not user.is_authenticated:
        return

    # Mark all existing concepts as not current
    GameConcept.objects.filter(user=user, is_current=True).update(is_current=False)

    # Create new current concept
    GameConcept.objects.create(
        user=user, content=game_text, is_current=True, last_sparc_evaluation=None
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
        "readiness_status": "Ready" | "Nearly Ready" | "Needs Work" | "Not Ready",
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
                mode="agentic",  # Explicitly use agentic mode for graph execution
            )

            # Execute through orchestrator (will use agent graph)
            response = self.orchestrator.execute(llm_request)

            if not response.success:
                error_messages = [err.message for err in response.errors]
                return JsonResponse(
                    {"error": "Evaluation failed", "details": error_messages},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Auto-save game concept after successful evaluation
            save_game_concept(request.user, game_text)

            return JsonResponse(response.results, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback

            traceback.print_exc()
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

            # Auto-save game concept after successful evaluation
            save_game_concept(request.user, game_text)

            return JsonResponse(response.results, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
