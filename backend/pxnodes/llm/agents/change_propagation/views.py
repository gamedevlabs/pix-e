import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import Project
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .workflow import ChangePropagationWorkflow

logger = logging.getLogger(__name__)


class ChangePropagationView(APIView):
    """Run change propagation analysis on a changed PxNode and return
    which other nodes in the project are semantically affected.

    POST /api/llm/propagation/check/
    {
        "project_id": <int or uuid>,
        "node_id": "<uuid>",
        "old_description": "...",
        "new_description": "...",
        "min_confidence": 0.5  (optional, float 0.0–1.0, default 0.5)
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data.get("project_id")
        node_id = request.data.get("node_id")
        old_description = request.data.get("old_description")
        new_description = request.data.get("new_description")

        missing = [
            field
            for field, val in [
                ("project_id", project_id),
                ("node_id", node_id),
                ("old_description", old_description),
                ("new_description", new_description),
            ]
            if val is None
        ]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            changed_node = PxNode.objects.get(id=node_id, project=project)
        except PxNode.DoesNotExist:
            return Response(
                {"error": "PxNode not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        min_confidence = float(request.data.get("min_confidence", 0.5))

        try:
            workflow = ChangePropagationWorkflow(model_manager=ModelManager())
            report = workflow.check_change(
                project=project,
                changed_node=changed_node,
                old_description=old_description,
                new_description=new_description,
                min_confidence=min_confidence,
            )
        except Exception:
            logger.exception(
                "ChangePropagationWorkflow failed for node '%s' in project '%s'",
                node_id,
                project_id,
            )
            return Response(
                {"error": "An unexpected error occurred during change propagation analysis."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(report.model_dump())
