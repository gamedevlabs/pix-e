"""
LLM Views for PxNodes.

Uses UserLLMOrchestratorMixin for per-user API key resolution.
"""

import logging
from typing import Any, Optional, cast

from django.contrib.auth.models import User
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from helpdesk.session_logging import buffer_backend_session_log
from llm import LLMOrchestrator
from llm.exceptions import OrchestratorError
from llm.logfire_config import get_logfire
from llm.mixins import UserLLMOrchestratorMixin
from llm.types import LLMRequest
from llm.view_utils import get_model_id
from projects.utils import get_current_project

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


class NodeFeedbackView(UserLLMOrchestratorMixin, ViewSet):
    """ViewSet for node LLM feedback operations using per-user API keys."""

    permission_classes = [permissions.IsAuthenticated]

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
                orchestrator = self.get_llm_orchestrator(request)

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

                response = orchestrator.execute(llm_request)

                logfire.info(
                    "nodes.validate.completed",
                    node_id=str(pk),
                    has_issues=response.results.get("has_issues", False),
                    issue_count=len(response.results.get("issues", [])),
                    coherence_score=response.results.get("overall_coherence_score"),
                )

                return JsonResponse(response.results, status=200)

            except APIException:
                raise
            except OrchestratorError as e:
                logger.warning("Orchestrator error for user=%s: %s", request.user.id, e)
                # Differentiate configuration errors from upstream provider failures
                error_message = str(e)
                if (
                    "No valid API keys" in error_message
                    or "No LLM providers" in error_message
                ):
                    return JsonResponse(
                        {
                            "error": "no_api_keys",
                            "detail": (
                                "No API keys configured. "
                                "Add an API key in Settings to enable AI features."
                            ),
                        },
                        status=400,
                    )
                if "not found in registry" in error_message:
                    return JsonResponse(
                        {
                            "error": "model_unavailable",
                            "detail": (
                                "The selected model is not available "
                                "with your current API keys."
                            ),
                        },
                        status=400,
                    )
                return JsonResponse({"error": error_message}, status=502)
            except Exception as e:
                buffer_backend_session_log(
                    session_id=getattr(request, "pixe_session_id", ""),
                    level="error",
                    event="pxnodes_llm.validate_node.fail",
                    message=str(e),
                    request=request,
                    metadata={
                        "node_id": pk,
                        "model": request.data.get("model"),
                        "validation_issue_count": len(
                            request.data.get("validation_issues", [])
                        ),
                    },
                )
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
                orchestrator = self.get_llm_orchestrator(request)

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

                response = orchestrator.execute(llm_request)

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

            except APIException:
                raise
            except OrchestratorError as e:
                logger.warning("Orchestrator error for user=%s: %s", request.user.id, e)
                error_message = str(e)
                if (
                    "No valid API keys" in error_message
                    or "No LLM providers" in error_message
                ):
                    return JsonResponse(
                        {
                            "error": "no_api_keys",
                            "detail": (
                                "No API keys configured. "
                                "Add an API key in Settings to enable AI features."
                            ),
                        },
                        status=400,
                    )
                if "not found in registry" in error_message:
                    return JsonResponse(
                        {
                            "error": "model_unavailable",
                            "detail": (
                                "The selected model is not available "
                                "with your current API keys."
                            ),
                        },
                        status=400,
                    )
                return JsonResponse({"error": error_message}, status=502)
            except Exception as e:
                buffer_backend_session_log(
                    session_id=getattr(request, "pixe_session_id", ""),
                    level="error",
                    event="pxnodes_llm.fix_node.fail",
                    message=str(e),
                    request=request,
                    metadata={
                        "node_id": pk,
                        "model": request.data.get("model"),
                        "validation_issue_count": len(
                            request.data.get("validation_issues", [])
                        ),
                    },
                )
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

            except APIException:
                raise
            except Exception as e:
                buffer_backend_session_log(
                    session_id=getattr(request, "pixe_session_id", ""),
                    level="error",
                    event="pxnodes_llm.accept_fix.fail",
                    message=str(e),
                    request=request,
                    metadata={
                        "node_id": pk,
                        "model": request.data.get("model"),
                        "validation_issue_count": len(
                            request.data.get("validation_issues", [])
                        ),
                    },
                )
                logger.exception(f"Error in accept_fix: {e}")
                logfire.error("nodes.accept_fix.error", error=str(e), node_id=pk)
                return JsonResponse({"error": str(e)}, status=500)
