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

from game_concept.utils import get_current_project
from llm import LLMOrchestrator
from llm.types import LLMRequest
from llm.view_utils import get_model_id

from .models import Pillar
from .serializers import PillarSerializer
from .utils import save_pillar_llm_call
from .view_utils import get_project_pillars

logger = logging.getLogger(__name__)


class PillarViewSet(ModelViewSet):
    serializer_class = PillarSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Pillar]:
        user = cast(User, self.request.user)
        return get_project_pillars(user)

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user = cast(User, self.request.user)
        serializer.save(user=user, project=get_current_project(user))


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

            user = cast(User, request.user)
            pillar = get_project_pillars(user).filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "gemini")

            llm_request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": pillar.name, "description": pillar.description},
                model_id=get_model_id(model),
            )

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="validate",
                response=response,
                pillar=pillar,
            )

            return JsonResponse(response.results, status=200)

        except Exception as e:
            logger.exception("Error in validate_pillar: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_pillar(self, request: Request, pk: Optional[int] = None) -> JsonResponse:
        try:
            if pk is None:
                return JsonResponse({"error": "Pillar ID is required"}, status=400)

            user = cast(User, request.user)
            pillar = get_project_pillars(user).filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            model = request.data.get("model", "openai")
            model_id = get_model_id(model)

            validation_issues = request.data.get("validation_issues", [])

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

            response = self.orchestrator.execute(llm_request)

            save_pillar_llm_call(
                user=user,
                operation="improve_explained",
                response=response,
                pillar=pillar,
            )

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
            logger.exception("Error in fix_pillar: %s", e)
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="accept-fix")
    def accept_fix(self, request: Request, pk: Optional[int] = None) -> JsonResponse:
        try:
            if pk is None:
                return JsonResponse({"error": "Pillar ID is required"}, status=400)

            user = cast(User, request.user)
            pillar = get_project_pillars(user).filter(id=pk).first()
            if not pillar:
                return JsonResponse({"error": "Pillar not found"}, status=404)

            name = request.data.get("name")
            description = request.data.get("description")

            if not name or not description:
                return JsonResponse(
                    {"error": "Missing required fields: 'name' and 'description'"},
                    status=400,
                )

            pillar.name = name
            pillar.description = description
            pillar.save()

            data = PillarSerializer(pillar).data
            return JsonResponse(data, status=200)

        except Exception as e:
            logger.exception("Error in accept_fix: %s", e)
            return JsonResponse({"error": str(e)}, status=500)
