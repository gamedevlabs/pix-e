import logging
from typing import Any, cast

from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from llm import LLMOrchestrator
from llm.logfire_config import get_logfire
from llm.types import LLMRequest
from llm.view_utils import get_model_id
from pillars.models import Pillar
from pillars.serializers import PillarSerializer
from pillars.utils import (
    save_agent_result_llm_call,
    save_execution_result_llm_calls,
    save_pillar_llm_call,
)
from pillars.llm import handlers, workflows  # noqa: F401

from .view_utils import (
    build_context_payload,
    build_context_payload_from_text,
    get_project_concept,
    get_project_pillars,
)

logger = logging.getLogger(__name__)


class LLMFeedbackView(ViewSet):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__()
        self.orchestrator = LLMOrchestrator()

    @action(detail=False, methods=["POST"], url_path="overall")
    def overall_feedback(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            game_concept = get_project_concept(user)
            pillars = list(get_project_pillars(user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            logfire = get_logfire()
            pillars_text, context_text = build_context_payload(pillars, game_concept)

            with logfire.span(
                "pillars.evaluate.overall.monolithic",
                feature="pillars",
                execution_mode="monolithic",
                pillars_count=len(pillars),
            ):
                pass

            completeness_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )
            contradictions_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )
            additions_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )

            completeness_response = self.orchestrator.execute(completeness_request)
            contradictions_response = self.orchestrator.execute(contradictions_request)
            additions_response = self.orchestrator.execute(additions_request)

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
            logger.exception("Error in overall_feedback: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="completeness")
    def completeness(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(get_project_pillars(user))
            game_concept = get_project_concept(user)

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload(pillars, game_concept)

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_completeness",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="evaluate_completeness",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception("Error in completeness: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="contradictions")
    def contradictions(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(get_project_pillars(user))
            game_concept = get_project_concept(user)

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload(pillars, game_concept)

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_contradictions",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="evaluate_contradictions",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception("Error in contradictions: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="additions")
    def additions(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(get_project_pillars(user))
            game_concept = get_project_concept(user)

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload(pillars, game_concept)

            llm_request = LLMRequest(
                feature="pillars",
                operation="suggest_additions",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="suggest_additions",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception("Error in additions: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="context")
    def context(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            pillars = list(get_project_pillars(user))
            context_text = request.data.get("context", "")

            if not context_text:
                return JsonResponse({"error": "No context provided"}, status=400)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload_from_text(
                pillars, context_text
            )

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_context",
                data={"pillars_text": pillars_text, "context": context_text},
                model_id=model_id,
            )

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="evaluate_context",
                response=response,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception("Error in context: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="evaluate-all")
    def evaluate_all(self, request: Request) -> JsonResponse:
        import asyncio

        try:
            user = cast(User, self.request.user)
            game_concept = get_project_concept(user)
            pillars = list(get_project_pillars(user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            if not pillars:
                return JsonResponse({"error": "No pillars found"}, status=404)

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload(pillars, game_concept)
            execution_mode = request.data.get("execution_mode", "agentic")

            if execution_mode not in ["monolithic", "agentic"]:
                return JsonResponse(
                    {"error": "execution_mode must be 'monolithic' or 'agentic'"},
                    status=400,
                )

            input_data = {"pillars_text": pillars_text, "context": context_text}

            logfire = get_logfire()

            if execution_mode == "monolithic":
                llm_request = LLMRequest(
                    feature="pillars",
                    operation="evaluate_comprehensive",
                    data=input_data,
                    model_id=model_id,
                )

                with logfire.span(
                    "pillars.evaluate.all.monolithic",
                    feature="pillars",
                    execution_mode="monolithic",
                ):
                    response = self.orchestrator.execute(llm_request)

                save_pillar_llm_call(
                    user=user,
                    operation="evaluate_comprehensive",
                    response=response,
                )

                result_data = response.results
                response_data = {
                    "execution_mode": "monolithic",
                    "concept_fit": {
                        "hasGaps": result_data.get("hasGaps", False),
                        "pillarFeedback": result_data.get("pillarFeedback", []),
                        "missingAspects": result_data.get("missingAspects", []),
                    },
                    "contradictions": {
                        "hasContradictions": result_data.get(
                            "hasContradictions", False
                        ),
                        "contradictions": result_data.get("contradictions", []),
                    },
                    "additions": (
                        {"additions": result_data.get("suggestedAdditions", [])}
                        if result_data.get("suggestedAdditions")
                        else None
                    ),
                    "resolution": (
                        {
                            "resolutions": result_data.get("resolutionSuggestions", []),
                            "overallRecommendation": result_data.get(
                                "overallFeedback", ""
                            ),
                        }
                        if result_data.get("resolutionSuggestions")
                        else None
                    ),
                    "overall": {
                        "score": result_data.get("overallScore", 3),
                        "feedback": result_data.get("overallFeedback", ""),
                    },
                    "metadata": {
                        "execution_time_ms": response.metadata.execution_time_ms,
                        "model_used": (
                            response.metadata.models_used[0].name
                            if response.metadata.models_used
                            else None
                        ),
                        "total_tokens": (
                            response.metadata.token_usage.total_tokens
                            if response.metadata.token_usage
                            else None
                        ),
                    },
                }

                return JsonResponse(response_data, status=200)

            from llm.agent_registry import get_workflow

            llm_request = LLMRequest(
                feature="pillars",
                operation="evaluate_all",
                data=input_data,
                model_id=model_id,
                mode="agentic",
            )

            workflow_class = get_workflow("pillars.evaluate_all")
            workflow = workflow_class(
                model_manager=self.orchestrator.model_manager,
                config=self.orchestrator.config,
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                with logfire.span(
                    "pillars.evaluate.all.agentic",
                    feature="pillars",
                    execution_mode="agentic",
                ):
                    result = loop.run_until_complete(workflow.run(llm_request))
            finally:
                loop.close()

            save_execution_result_llm_calls(
                user=user,
                result=result,
                input_data=input_data,
            )

            synthesis = result.aggregated_data.get("synthesis")
            response_data = {
                "execution_mode": "agentic",
                "concept_fit": result.aggregated_data.get("concept_fit"),
                "contradictions": result.aggregated_data.get("contradictions"),
                "additions": result.aggregated_data.get("additions"),
                "resolution": result.aggregated_data.get("resolution"),
                "overall": (
                    {
                        "score": synthesis.get("overallScore", 3),
                        "feedback": synthesis.get("overallFeedback", ""),
                        "strengths": synthesis.get("strengths", []),
                        "areasForImprovement": synthesis.get("areasForImprovement", []),
                    }
                    if synthesis
                    else None
                ),
                "metadata": {
                    "execution_time_ms": result.total_execution_time_ms,
                    "agents_run": [r.agent_name for r in result.agent_results],
                    "all_succeeded": result.success,
                },
            }

            return JsonResponse(response_data, status=200)

        except Exception as e:
            logger.exception("Error in evaluate_all: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="resolve-contradictions")
    def resolve_contradictions(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            game_concept = get_project_concept(user)
            pillars = list(get_project_pillars(user))

            if not game_concept:
                return JsonResponse({"error": "No game concept found"}, status=404)

            contradictions_data = request.data.get("contradictions")
            if not contradictions_data:
                return JsonResponse(
                    {"error": "No contradictions data provided"}, status=400
                )

            if not contradictions_data.get("hasContradictions"):
                return JsonResponse(
                    {"message": "No contradictions to resolve", "resolutions": []},
                    status=200,
                )

            model = request.data.get("model", "gemini")
            model_id = get_model_id(model)
            pillars_text, context_text = build_context_payload(pillars, game_concept)

            llm_request = LLMRequest(
                feature="pillars",
                operation="resolve_contradictions",
                data={
                    "pillars_text": pillars_text,
                    "context": context_text,
                    "contradictions_feedback": contradictions_data,
                },
                model_id=model_id,
            )

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

            input_data = {
                "pillars_text": pillars_text,
                "context": context_text,
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
            logger.exception("Error in resolve_contradictions: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["POST"], url_path="accept-addition")
    def accept_addition(self, request: Request) -> JsonResponse:
        try:
            user = cast(User, self.request.user)
            name = request.data.get("name")
            description = request.data.get("description")

            if not name or not description:
                return JsonResponse(
                    {"error": "Missing required fields: 'name' and 'description'"},
                    status=400,
                )

            pillar = Pillar.objects.create(
                user=user,
                name=name,
                description=description,
            )

            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=201)

        except Exception as e:
            logger.exception("Error in accept_addition: %s", e)
            return JsonResponse({"error": str(e)}, status=500)
