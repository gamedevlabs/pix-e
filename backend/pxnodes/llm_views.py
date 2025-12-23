"""
LLM Views for PxNodes.
"""

import logging
from typing import Any, Optional, cast

from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from game_concept.utils import get_current_project
from llm import LLMOrchestrator
from llm.logfire_config import get_logfire
from llm.types import LLMRequest
from llm.view_utils import get_model_id

# Import handlers to trigger auto-registration
from pxnodes.llm import handlers  # noqa: F401
from pxnodes.models import PxComponent, PxNode
from pxnodes.serializers import PxNodeSerializer

logger = logging.getLogger(__name__)
logfire = get_logfire()


def format_node_components(node: PxNode) -> list[dict[str, Any]]:
    """Format node components for LLM consumption."""
    components = []
    for comp in node.components.select_related("definition").all():
        components.append(
            {
                "component_id": str(comp.id),
                "definition_name": comp.definition.name,
                "definition_type": comp.definition.type,
                "value": comp.value,
            }
        )
    return components


class NodeFeedbackView(ViewSet):
    """ViewSet for node LLM feedback operations."""

    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.orchestrator = LLMOrchestrator()

    @action(detail=True, methods=["POST"], url_path="validate")
    def validate_node(self, request: Request, pk: Optional[str] = None) -> JsonResponse:
        """
        Validate a node for coherence issues.
        """
        with logfire.span("nodes.validate.view", node_id=pk):
            try:
                if pk is None:
                    return JsonResponse({"error": "Node ID is required"}, status=400)

                user = cast(User, request.user)
                project = get_current_project(user)
                node_filters: dict[str, Any] = {"id": pk}
                if project:
                    node_filters["project"] = project.id
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.filter(**node_filters).first()
                if not node:
                    return JsonResponse({"error": "Node not found"}, status=404)

                user = cast(User, request.user)
                if node.owner != user:
                    return JsonResponse({"error": "Not authorized"}, status=403)

                model = request.data.get("model", "gemini")
                components = format_node_components(node)

                llm_request = LLMRequest(
                    feature="nodes",
                    operation="validate",
                    data={
                        "name": node.name,
                        "description": node.description,
                        "components": components,
                    },
                    model_id=get_model_id(model),
                )

                response = self.orchestrator.execute(llm_request)

                logfire.info(
                    "nodes.validate.completed",
                    node_id=str(pk),
                    has_issues=response.results.get("has_issues", False),
                    issue_count=len(response.results.get("issues", [])),
                    coherence_score=response.results.get("overall_coherence_score"),
                )

                return JsonResponse(response.results, status=200)

            except Exception as e:
                logger.exception(f"Error in validate_node: {e}")
                logfire.error("nodes.validate.error", error=str(e), node_id=pk)
                return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="fix")
    def fix_node(self, request: Request, pk: Optional[str] = None) -> JsonResponse:
        """
        Generate an improved node with explanations.
        """
        with logfire.span("nodes.fix.view", node_id=pk):
            try:
                if pk is None:
                    return JsonResponse({"error": "Node ID is required"}, status=400)

                user = cast(User, request.user)
                project = get_current_project(user)
                node_filters: dict[str, Any] = {"id": pk}
                if project:
                    node_filters["project"] = project.id
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.filter(**node_filters).first()
                if not node:
                    return JsonResponse({"error": "Node not found"}, status=404)

                user = cast(User, request.user)
                if node.owner != user:
                    return JsonResponse({"error": "Not authorized"}, status=403)

                model = request.data.get("model", "gemini")
                model_id = get_model_id(model)
                validation_issues = request.data.get("validation_issues", [])
                components = format_node_components(node)

                llm_request = LLMRequest(
                    feature="nodes",
                    operation="improve_explained",
                    data={
                        "name": node.name,
                        "description": node.description,
                        "components": components,
                        "validation_issues": validation_issues,
                    },
                    model_id=model_id,
                )

                response = self.orchestrator.execute(llm_request)

                logfire.info(
                    "nodes.fix.completed",
                    node_id=str(pk),
                    changes_count=len(response.results.get("changes", [])),
                    component_changes_count=len(
                        response.results.get("component_changes", [])
                    ),
                )

                return JsonResponse(
                    {
                        "node_id": str(node.id),
                        "original": {
                            "name": node.name,
                            "description": node.description,
                            "components": components,
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
                logger.exception(f"Error in fix_node: {e}")
                logfire.error("nodes.fix.error", error=str(e), node_id=pk)
                return JsonResponse({"error": str(e)}, status=500)

    @action(detail=True, methods=["POST"], url_path="accept-fix")
    def accept_fix(self, request: Request, pk: Optional[str] = None) -> JsonResponse:
        """
        Accept and persist an AI-generated improvement.
        """
        with logfire.span("nodes.accept_fix.view", node_id=pk):
            try:
                if pk is None:
                    return JsonResponse({"error": "Node ID is required"}, status=400)

                user = cast(User, request.user)
                project = get_current_project(user)
                node_filters: dict[str, Any] = {"id": pk}
                if project:
                    node_filters["project"] = project.id
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.filter(**node_filters).first()
                if not node:
                    return JsonResponse({"error": "Node not found"}, status=404)

                user = cast(User, request.user)
                if node.owner != user:
                    return JsonResponse({"error": "Not authorized"}, status=403)

                name = request.data.get("name")
                description = request.data.get("description")
                component_updates = request.data.get("components", [])

                if not name or not description:
                    return JsonResponse(
                        {"error": "Missing required fields: 'name' and 'description'"},
                        status=400,
                    )

                # Update node name and description
                node.name = name
                node.description = description
                node.save()

                # Update component values if provided
                updated_components = []
                for comp_update in component_updates:
                    comp_id = comp_update.get("id")
                    new_value = comp_update.get("value")

                    if comp_id is not None and new_value is not None:
                        component = PxComponent.objects.filter(
                            id=comp_id, node=node, owner=user
                        ).first()
                        if component:
                            component.value = new_value
                            component.save()
                            updated_components.append(str(comp_id))

                logfire.info(
                    "nodes.accept_fix.completed",
                    node_id=str(pk),
                    components_updated=len(updated_components),
                )

                data = PxNodeSerializer(node).data
                return JsonResponse(data, status=200)

            except Exception as e:
                logger.exception(f"Error in accept_fix: {e}")
                logfire.error("nodes.accept_fix.error", error=str(e), node_id=pk)
                return JsonResponse({"error": str(e)}, status=500)
