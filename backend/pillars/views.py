import logging
from typing import Any, Optional, cast

from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet, ViewSet

from game_concept.models import GameConcept
from llm import LLMOrchestrator
from llm.types import LLMRequest
from llm.view_utils import get_model_id

# Import handlers to trigger auto-registration
from pillars.llm import handlers  # noqa: F401

from .models import Pillar
from .serializers import PillarSerializer
from .utils import (
    save_agent_result_llm_call,
    save_execution_result_llm_calls,
    save_pillar_llm_call,
)

logger = logging.getLogger(__name__)

# Create your views here.


def format_pillars_text(pillars: list[Pillar]) -> str:
    """Format pillars as text for orchestrator.

    Uses actual database IDs so the LLM can reference them correctly.
    """
    return "\n".join([f"[ID: {p.id}] {p.name}: {p.description}" for p in pillars])


class PillarViewSet(ModelViewSet):
    serializer_class = PillarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Pillar]:
        user = cast(User, self.request.user)
        return Pillar.objects.filter(user=user)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user = cast(User, self.request.user)
        serializer.save(user=user)


class PillarFeedbackView(ViewSet):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.orchestrator = LLMOrchestrator()

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate_pillar(
        self, request: Request, pk: Optional[int] = None
    ) -> JsonResponse:
        try:
            if pk is None:
                return JsonResponse({"error": "Pillar ID is required"}, status=400)

            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "gemini")

            # Create orchestrator request
            llm_request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": pillar.name, "description": pillar.description},
                model_id=get_model_id(model),
            )

            # Execute through orchestrator
            response = self.orchestrator.execute(llm_request)

            # Save metrics
            user = cast(User, request.user)
            save_pillar_llm_call(
                user=user,
                operation="validate",
                response=response,
                pillar=pillar,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception(f"Error in validate_pillar: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_pillar(self, request: Request, pk: Optional[int] = None) -> JsonResponse:
        """
        Generate an improved pillar with explanations.

        Expects request body:
        {
            "model": "gemini" | "openai | "ollama",
            "validation_issues": [{"title": "...", "description": "..."}]  # optional
        }

        Returns enriched response with original, improved, and explanations.
        """
        try:
            if pk is None:
                return JsonResponse({"error": "Pillar ID is required"}, status=400)

            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "openai")
            model_id = get_model_id(model)

            # Get validation issues from request (frontend caches these)
            validation_issues = request.data.get("validation_issues", [])

            # Create orchestrator request with explanation handler
            llm_request = LLMRequest(
                feature="pillars",
                operation="improve_explained",
                data={
                    "name": pillar.name,
                    "description": pillar.description,
                    "validation_issues": validation_issues,
                },
                model_id=model_id,
            )

            # Execute through orchestrator
            response = self.orchestrator.execute(llm_request)

            # Save metrics
            user = cast(User, request.user)
            save_pillar_llm_call(
                user=user,
                operation="improve_explained",
                response=response,
                pillar=pillar,
            )

            # Return enriched response (don't save - user decides)
            return JsonResponse(
                {
                    "pillar_id": pillar.id,
                    "original": {
                        "name": pillar.name,
                        "description": pillar.description,
                    },
                    "improved": response.results,
                    "metadata": {
                        "execution_time_ms": response.metadata.execution_time_ms,
                        "model_used": (
                            response.metadata.models_used[0].name
                            if response.metadata.models_used
                            else None
                        ),
                    },
                },
                status=200,
            )

        except Exception as e:
            logger.exception(f"Error in fix_pillar: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="accept-fix")
    def accept_fix(self, request: Request, pk: Optional[int] = None) -> JsonResponse:
        """
        Accept and persist an AI-generated improvement.

        Expects request body:
        {
            "name": "...",
            "description": "..."
        }
        """
        try:
            if pk is None:
                return JsonResponse({"error": "Pillar ID is required"}, status=400)

            pillar = Pillar.objects.filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            # Validate required fields
            name = request.data.get("name")
            description = request.data.get("description")

            if not name or not description:
                return JsonResponse(
                    {"error": "Missing required fields: 'name' and 'description'"},
                    status=400,
                )

            # Update pillar with accepted improvement
            pillar.name = name
            pillar.description = description
            pillar.save()

            # Return updated pillar
            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=200)

        except Exception as e:
            logger.exception(f"Error in accept_fix: {e}")
            return JsonResponse({"error": str(e)}, status=500)


class LLMFeedbackView(ViewSet):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.orchestrator = LLMOrchestrator()

    @action(detail=False, methods=["POST"], url_path="overall")
    def overall_feedback(self, request: Request) -> JsonResponse:
        """
        Overall feedback - calls 3 operations sequentially.
        This replicates the old evaluate_pillars_in_context behavior.
        """
        try:
            user = cast(User, self.request.user)
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()
            pillars = list(Pillar.objects.filter(user=user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text = format_pillars_text(pillars)

            completeness_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={"pillars_text": pillars_text, "context": game_concept.content},
                model_id=model_id,
            )
            contradictions_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={"pillars_text": pillars_text, "context": game_concept.content},
                model_id=model_id,
            )
            additions_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={"pillars_text": pillars_text, "context": game_concept.content},
                model_id=model_id,
            )

            completeness_response = self.orchestrator.execute(completeness_request)
            contradictions_response = self.orchestrator.execute(contradictions_request)
            additions_response = self.orchestrator.execute(additions_request)

            # Save metrics for each call
            save_pillar_llm_call(
                user=user,
                operation="evaluate_completeness",
                response=completeness_response,
            )
            save_pillar_llm_call(
                user=user,
                operation="evaluate_contradictions",
                response=contradictions_response,
            )
            save_pillar_llm_call(
                user=user,
                operation="suggest_additions",
                response=additions_response,
            )

            combined_result = {
                "coverage": completeness_response.results,
                "contradictions": contradictions_response.results,
                "proposedAdditions": additions_response.results,
            }

            return JsonResponse(combined_result, status=200)

        except Exception as e:
            logger.exception(f"Error in overall_feedback: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="completeness")
    def completeness(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(Pillar.objects.filter(user=user))
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": game_concept.content,
                },
                model_id=get_model_id(model),
            )

            response = self.orchestrator.execute(llm_request)

            # Save metrics
            save_pillar_llm_call(
                user=user,
                operation="evaluate_completeness",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception(f"Error in completeness: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="contradictions")
    def contradictions(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(Pillar.objects.filter(user=user))
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": game_concept.content,
                },
                model_id=get_model_id(model),
            )

            response = self.orchestrator.execute(llm_request)

            # Save metrics
            save_pillar_llm_call(
                user=user,
                operation="evaluate_contradictions",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception(f"Error in contradictions: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="additions")
    def additions(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(Pillar.objects.filter(user=user))
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": game_concept.content,
                },
                model_id=get_model_id(model),
            )

            response = self.orchestrator.execute(llm_request)

            # Save metrics
            save_pillar_llm_call(
                user=user,
                operation="suggest_additions",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception(f"Error in additions: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="context")
    def context(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(Pillar.objects.filter(user=user))
            context_text = request.data.get("context", "")

            if not context_text:
                return JsonResponse({"error": "No context provided"}, status=400)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_context",
                data={
                    "pillars_text": format_pillars_text(pillars),
                    "context": context_text,
                },
                model_id=get_model_id(model),
            )

            response = self.orchestrator.execute(llm_request)

            # Save metrics
            save_pillar_llm_call(
                user=user,
                operation="evaluate_context",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception(f"Error in context: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="evaluate-all")
    def evaluate_all(self, request: Request) -> JsonResponse:
        """
        Run comprehensive pillar evaluation using agent workflow.

        Execution flow:
        1. Run ConceptFit and Contradictions agents in parallel
        2. If gaps found: auto-run SuggestAdditions with concept fit context
        3. If contradictions found: auto-run ContradictionResolution

        Returns all results in a unified response.
        """
        import asyncio

        from llm.agent_registry import get_workflow

        try:
            user = cast(User, self.request.user)
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()
            pillars = list(Pillar.objects.filter(user=user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            if not pillars:
                return JsonResponse({"error": "No pillars found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text = format_pillars_text(pillars)

            # Create request for the workflow
            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_all",
                data={
                    "pillars_text": pillars_text,
                    "context": game_concept.content,
                },
                model_id=model_id,
                mode="agentic",
            )

            # Get the workflow and run it
            workflow_class = get_workflow("pillars.evaluate_all")
            workflow = workflow_class(
                model_manager=self.orchestrator.model_manager,
                config=self.orchestrator.config,
            )

            # Run the async workflow
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(workflow.run(llm_request))
            finally:
                loop.close()

            # Save LLM calls (aggregated + per-agent)
            input_data = {
                "pillars_text": pillars_text,
                "context": game_concept.content,
            }
            save_execution_result_llm_calls(
                user=user,
                result=result,
                input_data=input_data,
            )

            # Build response
            response_data = {
                "concept_fit": result.aggregated_data.get("concept_fit"),
                "contradictions": result.aggregated_data.get("contradictions"),
                "additions": result.aggregated_data.get("additions"),
                "resolution": result.aggregated_data.get("resolution"),
                "metadata": {
                    "execution_time_ms": result.total_execution_time_ms,
                    "agents_run": [r.agent_name for r in result.agent_results],
                    "all_succeeded": result.success,
                },
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            logger.exception(f"Error in evaluate_all: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="resolve-contradictions")
    def resolve_contradictions(self, request: Request) -> JsonResponse:
        """
        Suggest resolutions for detected contradictions.

        Expects request body:
        {
            "model": "gemini" | "openai",
            "contradictions": {
                "hasContradictions": true,
                "contradictions": [...]
            }
        }

        The contradictions object should be the output from the contradictions endpoint.
        """
        try:
            user = cast(User, self.request.user)
            game_concept = GameConcept.objects.filter(
                user=user, is_current=True
            ).first()
            pillars = list(Pillar.objects.filter(user=user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            contradictions_data = request.data.get("contradictions")
            if not contradictions_data:
                return JsonResponse(
                    {"error": "No contradictions data provided"}, status=400
                )

            # Check if there are actually contradictions to resolve
            if not contradictions_data.get("hasContradictions"):
                return JsonResponse(
                    {"message": "No contradictions to resolve", "resolutions": []},
                    status=200,
                )

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text = format_pillars_text(pillars)

            # Use the contradiction resolution handler
            llm_request = LLMRequest(
                feature="pillars",
                operation="resolve_contradictions",
                data={
                    "pillars_text": pillars_text,
                    "context": game_concept.content,
                    "contradictions_feedback": contradictions_data,
                },
                model_id=model_id,
            )

            # Run the contradiction resolution agent directly
            import asyncio

            from pillars.llm.agents import ContradictionResolutionAgent

            agent = ContradictionResolutionAgent()
            context = {
                "model_manager": self.orchestrator.model_manager,
                "data": llm_request.data,
                "model_id": model_id,
                "model_preference": "auto",
            }

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(agent.run(context))
            finally:
                loop.close()

            if not result.success:
                return JsonResponse(
                    {"error": "Failed to generate resolution suggestions"},
                    status=500,
                )

            # Save LLM call
            input_data = {
                "pillars_text": pillars_text,
                "context": game_concept.content,
                "contradictions_feedback": contradictions_data,
            }
            save_agent_result_llm_call(
                user=user,
                operation="resolve_contradictions",
                result=result,
                input_data=input_data,
            )

            return JsonResponse(result.data, status=200)

        except Exception as e:
            logger.exception(f"Error in resolve_contradictions: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="accept-addition")
    def accept_addition(self, request: Request) -> JsonResponse:
        """
        Accept a suggested pillar and create it in the database.

        Expects request body:
        {
            "name": "...",
            "description": "..."
        }
        """
        try:
            user = cast(User, self.request.user)
            name = request.data.get("name")
            description = request.data.get("description")

            if not name or not description:
                return JsonResponse(
                    {"error": "Missing required fields: 'name' and 'description'"},
                    status=400,
                )

            # Create new pillar
            pillar = Pillar.objects.create(
                user=user,
                name=name,
                description=description,
            )

            # Return serialized pillar
            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=201)

        except Exception as e:
            logger.exception(f"Error in accept_addition: {e}")
            return JsonResponse({"error": str(e)}, status=500)
