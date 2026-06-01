from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import Project
from llm.mixins import UserLLMOrchestratorMixin

from .workflow import ConsistencyWorkflow


class ConsistencyCheckView(UserLLMOrchestratorMixin, APIView):
    """Run consistency checks on a project and return the findings.

    Uses per-user API keys via UserLLMOrchestratorMixin.

    POST /api/llm/consistency/check/
    {
        "project_id": "<uuid>",
        "min_confidence": 0.0  (optional, float 0.0–1.0, default 0.0)
    }

    Semantic findings whose confidence is below min_confidence are omitted.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data.get("project_id")
        if not project_id:
            return Response(
                {"error": "project_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        min_confidence = float(request.data.get("min_confidence", 0.0))
        orchestrator = self.get_llm_orchestrator(request)
        workflow = ConsistencyWorkflow(
            model_manager=orchestrator.model_manager,
            min_confidence=min_confidence,
        )
        report = workflow.check_project(project)
        return Response(report.model_dump())
