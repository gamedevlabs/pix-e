import logging
import re

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import Project
from llm.exceptions import RateLimitError
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .fix_agent import ConsistencyFixAgent
from .workflow import ConsistencyWorkflow

logger = logging.getLogger(__name__)


class ConsistencyCheckView(APIView):
    """Run consistency checks on a project and return the findings.

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
        workflow = ConsistencyWorkflow(
            model_manager=ModelManager(),
            min_confidence=min_confidence,
        )
        try:
            report = workflow.check_project(project)
        except RateLimitError:
            return Response(
                {"error": "Rate limit reached. Please wait and try again."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return Response(report.model_dump())


class ConsistencyFixView(APIView):
    """Suggest a corrected description for a node with a consistency finding.

    POST /api/llm/consistency/fix/
    {
        "project_id": "<uuid>",
        "node_id": "<uuid>",
        "finding_category": "...",
        "finding_description": "..."
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data.get("project_id")
        node_id = request.data.get("node_id")
        finding_category = request.data.get("finding_category")
        finding_description = request.data.get("finding_description")

        missing = [
            field
            for field, val in [
                ("project_id", project_id),
                ("node_id", node_id),
                ("finding_category", finding_category),
                ("finding_description", finding_description),
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
            node = PxNode.objects.get(id=node_id, project=project)
        except PxNode.DoesNotExist:
            return Response(
                {"error": "PxNode not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        other_nodes = list(
            project.pxnodes.exclude(id=node.id).values("name", "description")
        )

        agent_data: dict = {
            "node_name": node.name,
            "node_description": node.description,
            "finding_category": finding_category,
            "finding_description": finding_description,
            "other_nodes": other_nodes,
        }

        if finding_category == "pillar_misalignment":
            pillar = self._extract_pillar(project, finding_description)
            if pillar:
                agent_data["pillar_name"] = pillar.name
                agent_data["pillar_description"] = pillar.description

        elif finding_category == "node_contradiction":
            agent_data["pillars_section"] = self._format_pillars(project)

        try:
            agent = ConsistencyFixAgent()
            context = {
                "model_manager": ModelManager(),
                "data": agent_data,
            }
            result = agent.execute(context)
        except Exception:
            logger.exception(
                "ConsistencyFixAgent failed for node '%s' in project '%s'",
                node_id,
                project_id,
            )
            return Response(
                {"error": "An unexpected error occurred during fix generation."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not result.success:
            error_msg = result.error.message if result.error else "unknown error"
            logger.error(
                "ConsistencyFixAgent failed for node '%s' in project '%s': %s",
                node_id,
                project_id,
                error_msg,
            )
            if "rate limit" in error_msg.lower():
                return Response(
                    {"error": "Rate limit reached. Please wait a moment and try again."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return Response(
                {"error": f"Fix generation failed: {error_msg}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not result.data:
            logger.error(
                "ConsistencyFixAgent returned empty data for node '%s'", node_id
            )
            return Response(
                {"error": "Fix generation returned no suggestion."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "node_id": str(node.id),
                "original_description": node.description,
                "suggested_description": result.data["suggested_description"],
            }
        )

    def _extract_pillar(self, project, finding_description: str):
        """Parse the pillar UUID from a pillar_misalignment message and load it."""
        match = re.match(r"\[pillar ([^\]]+)\]", finding_description)
        if not match:
            return None
        pillar_id = match.group(1).strip()
        try:
            return project.pillars.get(id=pillar_id)
        except Exception:
            return None

    def _format_pillars(self, project) -> str:
        """Return a compact pillar list for node_contradiction context."""
        pillars = list(project.pillars.all())
        if not pillars:
            return "No design pillars defined."
        return "\n".join(f"- {p.name}: {p.description}" for p in pillars)
