"""
SPARC API views.

Provides endpoints for both agentic (quick scan) and monolithic
SPARC evaluations.
"""

from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from backend.llm import LLMOrchestrator, get_config
from backend.llm.types import LLMRequest, LLMResponse
from game_concept.models import GameConcept

# Import handlers and graphs to trigger auto-registration
from sparc.llm import graphs, handlers  # noqa: F401
from sparc.models import SPARCEvaluation, SPARCEvaluationResult


def get_model_id(model_name: str) -> str:
    """
    Map frontend model names to actual model IDs using config.
    """
    config = get_config()
    return config.resolve_model_alias(model_name)


def calculate_cost_eur(
    model_name: str, prompt_tokens: int = 0, completion_tokens: int = 0
) -> float:
    """
    Calculate cost in EUR based on actual token usage and model pricing.

    Args:
        model_name: Name of the model used
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Cost in EUR (8 decimal precision)
    """
    # Model costs per 1M tokens in EUR
    # Based on current pricing (converted from USD at ~0.90 EUR/USD)
    MODEL_COSTS = {
        "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free
        "gpt-4o-mini": {
            "input": 0.135,
            "output": 0.540,
        },  # $0.150/$0.600
        "gpt-4o": {"input": 2.25, "output": 9.00},  # $2.50/$10.00
    }

    costs = MODEL_COSTS.get(model_name, {"input": 0.0, "output": 0.0})

    input_cost = (prompt_tokens / 1_000_000) * costs["input"]
    output_cost = (completion_tokens / 1_000_000) * costs["output"]

    return round(input_cost + output_cost, 8)


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
                    aspect_data.get("completeness_score")
                    if isinstance(aspect_data, dict)
                    else None
                )

                SPARCEvaluationResult.objects.create(
                    evaluation=evaluation,
                    aspect=aspect_mapping[aspect_key],
                    score=score,
                    agent_name=agent.name,
                    model_used=agent.model,
                    execution_time_ms=agent.execution_time_ms,
                    result_data=aspect_data,
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

            # Save evaluation to database
            context = request.data.get("context", "")
            evaluation = save_sparc_evaluation(
                game_text, context, "monolithic", response
            )

            # Auto-save game concept with linked evaluation
            save_game_concept(request.user, game_text, evaluation)

            return JsonResponse(response.results, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
