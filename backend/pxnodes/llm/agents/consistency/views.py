"""REST API view for the Consistency Agent."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import Project

from .workflow import ConsistencyWorkflow


class ConsistencyCheckView(APIView):
    """Run consistency checks on a project and return the findings.

    POST /api/llm/consistency/check/
    { "project_id": "<uuid>" }
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

        report = ConsistencyWorkflow().check_project(project)
        return Response(report.model_dump())
