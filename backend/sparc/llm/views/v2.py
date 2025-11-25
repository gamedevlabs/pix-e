"""
SPARC V2 API views.

Router-based agentic evaluation endpoints.
"""

import asyncio
from typing import List, Optional

from django.http import JsonResponse
from rest_framework import permissions, status
from rest_framework.views import APIView

from game_concept.models import GameConcept
from llm.config import get_config
from llm.events import EventCollector
from llm.providers.manager import ModelManager

# Import to trigger graph registration
from sparc.llm import graphs, graphs_v2  # noqa: F401
from sparc.llm.graphs_v2 import SPARCRouterGraph
from sparc.models import SPARCEvaluation

VALID_PILLAR_MODES = {"all", "filtered", "none"}


def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs using config."""
    config = get_config()
    return config.resolve_model_alias(model_name)


def save_game_concept(user, game_text: str, evaluation=None) -> None:
    """Auto-save game concept after SPARC evaluation."""
    if not user.is_authenticated:
        return

    GameConcept.objects.filter(user=user, is_current=True).update(is_current=False)
    GameConcept.objects.create(
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

    def post(self, request):
        """Execute full V2 evaluation."""
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
            pillar_mode = request.data.get("pillar_mode", "filtered")
            if pillar_mode not in VALID_PILLAR_MODES:
                return JsonResponse(
                    {"error": "Invalid pillar_mode"},
                    status=status.HTTP_400_BAD_REQUEST,
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

            # Execute graph
            result = self._execute_graph(
                game_text=game_text,
                context_text=context_text,
                model_id=model_id,
                mode="full",
                evaluation=evaluation,
                pillar_mode=pillar_mode,
                user=request.user if request.user.is_authenticated else None,
            )

            if not result["success"]:
                return JsonResponse(
                    {"error": "Evaluation failed", "details": result.get("errors", [])},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Update evaluation with totals
            aggregated = result["aggregated_data"]
            evaluation.execution_time_ms = aggregated.get("execution_time_ms", 0)
            evaluation.total_tokens = aggregated.get("total_tokens", 0)
            evaluation.estimated_cost_eur = aggregated.get("estimated_cost_eur", 0)
            evaluation.save()

            # Auto-save game concept
            save_game_concept(request.user, game_text, evaluation)

            return JsonResponse(aggregated, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _execute_graph(
        self,
        game_text: str,
        context_text: str,
        model_id: str,
        mode: str,
        evaluation: SPARCEvaluation,
        pillar_mode: str,
        user,
        target_aspects: Optional[List[str]] = None,
    ) -> dict:
        """Execute the V2 graph."""
        from llm.types import LLMRequest

        config = get_config()
        model_manager = ModelManager(config)
        event_collector = EventCollector()

        graph = SPARCRouterGraph(
            model_manager=model_manager,
            config=config,
            event_collector=event_collector,
            evaluation=evaluation,
            user=user,
        )

        request = LLMRequest(
            feature="sparc",
            operation="router_v2",
            data={
                "game_text": game_text,
                "context": context_text,
                "pillar_mode": pillar_mode,
            },
            model_id=model_id,
            mode="agentic",
        )

        # Run async graph in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                graph.run(request, mode=mode, target_aspects=target_aspects)
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

    def post(self, request):
        """Execute single or multiple aspect evaluation."""
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
            pillar_mode = request.data.get("pillar_mode", "filtered")
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

            # Execute graph
            result = self._execute_graph(
                game_text=game_text,
                context_text=context_text,
                model_id=model_id,
                mode=mode,
                evaluation=evaluation,
                pillar_mode=pillar_mode,
                user=request.user if request.user.is_authenticated else None,
                target_aspects=target_aspects,
            )

            if not result["success"]:
                return JsonResponse(
                    {"error": "Evaluation failed", "details": result.get("errors", [])},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Update evaluation with totals
            aggregated = result["aggregated_data"]
            evaluation.execution_time_ms = aggregated.get("execution_time_ms", 0)
            evaluation.total_tokens = aggregated.get("total_tokens", 0)
            evaluation.estimated_cost_eur = aggregated.get("estimated_cost_eur", 0)
            evaluation.save()

            return JsonResponse(aggregated, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _execute_graph(
        self,
        game_text: str,
        context_text: str,
        model_id: str,
        mode: str,
        evaluation: SPARCEvaluation,
        pillar_mode: str,
        user,
        target_aspects: List[str],
    ) -> dict:
        """Execute the V2 graph for specific aspects."""
        from llm.types import LLMRequest

        config = get_config()
        model_manager = ModelManager(config)
        event_collector = EventCollector()

        graph = SPARCRouterGraph(
            model_manager=model_manager,
            config=config,
            event_collector=event_collector,
            evaluation=evaluation,
            user=user,
        )

        request = LLMRequest(
            feature="sparc",
            operation="router_v2",
            data={
                "game_text": game_text,
                "context": context_text,
                "pillar_mode": pillar_mode,
            },
            model_id=model_id,
            mode="agentic",
        )

        # Run async graph in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                graph.run(request, mode=mode, target_aspects=target_aspects)
            )
        finally:
            loop.close()

        return {
            "success": result.success,
            "aggregated_data": result.aggregated_data,
            "errors": [e.message for e in result.errors] if result.errors else [],
        }
