import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import Project
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .fix_agent import ChangePropagationFixAgent
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
        use_graph_context = bool(request.data.get("use_graph_context", False))
        max_depth = int(request.data.get("max_depth", 3))
        # Mirror the consistency view: pin the agent to gpt-5.4-mini so the
        # production endpoint matches the evaluated model. Without this the
        # workflow falls back to the orchestrator's "auto" default (gpt-3.5-turbo).
        model_id = "gpt-5.4-mini-2026-03-17"

        try:
            workflow = ChangePropagationWorkflow(model_manager=ModelManager())
            report = workflow.check_change(
                project=project,
                changed_node=changed_node,
                old_description=old_description,
                new_description=new_description,
                min_confidence=min_confidence,
                use_graph_context=use_graph_context,
                max_depth=max_depth,
                model_id=model_id,
            )
        except Exception:
            logger.exception(
                "ChangePropagationWorkflow failed for node '%s' in project '%s'",
                node_id,
                project_id,
            )
            return Response(
                {
                    "error": (
                        "An unexpected error occurred during"
                        " change propagation analysis."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(report.model_dump())


class ChangePropagationFixView(APIView):
    """Suggest a corrected description for a node affected by a change.

    POST /api/llm/propagation/fix/
    {
        "affected_node_id": "<uuid>",
        "changed_node_id": "<uuid>",
        "changed_node_old_description": "...",
        "changed_node_new_description": "..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        affected_node_id = request.data.get("affected_node_id")
        changed_node_id = request.data.get("changed_node_id")
        changed_node_old_description = request.data.get("changed_node_old_description")
        changed_node_new_description = request.data.get("changed_node_new_description")

        missing = [
            field
            for field, val in [
                ("affected_node_id", affected_node_id),
                ("changed_node_id", changed_node_id),
                ("changed_node_old_description", changed_node_old_description),
                ("changed_node_new_description", changed_node_new_description),
            ]
            if val is None
        ]
        if missing:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            affected_node = PxNode.objects.get(id=affected_node_id)
        except PxNode.DoesNotExist:
            return Response(
                {"error": "Affected node not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            changed_node = PxNode.objects.get(id=changed_node_id)
        except PxNode.DoesNotExist:
            return Response(
                {"error": "Changed node not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        agent_data = {
            "changed_node_name": changed_node.name,
            "changed_node_old_description": changed_node_old_description,
            "changed_node_new_description": changed_node_new_description,
            "affected_node_name": affected_node.name,
            "affected_node_current_description": affected_node.description,
        }

        try:
            result = ChangePropagationFixAgent().fix(agent_data)
        except Exception as e:
            if "rate limit" in str(e).lower():
                return Response(
                    {"error": "Rate limit reached. Please wait and try again."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            logger.exception(
                "ChangePropagationFixAgent failed for affected node '%s'",
                affected_node_id,
            )
            return Response(
                {"error": "Fix generation failed."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "node_id": str(affected_node.id),
                "original": {
                    "name": affected_node.name,
                    "description": affected_node.description,
                },
                "improved": {
                    # Change propagation never renames the affected node.
                    "name": affected_node.name,
                    "description": result["improved_description"],
                    "changes": result.get("changes", []),
                    "overall_summary": result.get("overall_summary", ""),
                    "issues_fixed": result.get("issues_fixed", []),
                },
            }
        )
