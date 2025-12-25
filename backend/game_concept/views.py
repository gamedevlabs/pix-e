"""
Views for the game_concept app.
"""

import uuid
from typing import Any, Optional, Type, cast

from django.contrib.auth.models import User
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from pillars.models import Pillar
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode

from .models import GameConcept, Project
from .serializers import (
    GameConceptCreateSerializer,
    GameConceptListSerializer,
    GameConceptSerializer,
    ProjectSerializer,
)
from .utils import get_current_game_concept, get_current_project


class GameConceptViewSet(ModelViewSet):
    """
    ViewSet for managing game concepts.

    Endpoints:
    - GET /api/game-concept/ - List all concepts for the user
    - GET /api/game-concept/current/ - Get current concept
    - GET /api/game-concept/history/ - Get concept history
    - POST /api/game-concept/ - Create new concept
    - GET /api/game-concept/{id}/ - Get specific concept
    - PUT/PATCH /api/game-concept/{id}/ - Update concept
    - DELETE /api/game-concept/{id}/ - Delete concept
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[GameConcept]:
        """Return concepts for the current user."""
        user = cast(User, self.request.user)
        project = get_current_project(user)
        if project:
            return GameConcept.objects.filter(user=user, project=project)
        return GameConcept.objects.none()

    def get_serializer_class(self) -> Type[Serializer[Any]]:
        """Return appropriate serializer based on action."""
        if self.action == "create":
            return GameConceptCreateSerializer
        elif self.action == "list" or self.action == "history":
            return GameConceptListSerializer
        return GameConceptSerializer

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Create a new game concept with user from request."""
        serializer.save()

    @action(detail=False, methods=["get"])
    def current(self, request: Request) -> Response:
        """
        Get the current game concept for the user.

        Returns 404 if no current concept exists.
        """
        user = cast(User, request.user)
        try:
            concept = get_current_game_concept(get_current_project(user))
            if not concept:
                raise GameConcept.DoesNotExist
            serializer = GameConceptSerializer(concept)
            return Response(serializer.data)
        except GameConcept.DoesNotExist:
            return Response(
                {"detail": "No current game concept found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def history(self, request: Request) -> Response:
        """
        Get all past game concepts for the user (including current).

        Returns list ordered by most recent first.
        Uses full serializer to include complete content.
        """
        user = cast(User, request.user)
        project = get_current_project(user)
        if not project:
            return Response([], status=status.HTTP_200_OK)
        concepts = GameConcept.objects.filter(project=project).order_by("-updated_at")

        serializer = GameConceptSerializer(concepts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_current(self, request: Request) -> Response:
        """
        Update or create the current game concept.

        Marks all existing concepts as not current and creates
        a new current concept with the provided content.
        """
        user = cast(User, request.user)
        content = request.data.get("content")
        if not content:
            return Response(
                {"error": "Content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_current_project(user)
        if not project:
            project = Project.objects.create(user=user, name="Untitled Project")

        # Mark all existing concepts as not current
        GameConcept.objects.filter(project=project, is_current=True).update(
            is_current=False
        )

        # Create new current concept
        concept = GameConcept.objects.create(
            user=user, project=project, content=content, is_current=True
        )

        serializer = GameConceptSerializer(concept)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def restore(self, request: Request, pk: Optional[int] = None) -> Response:
        """
        Restore a past game concept as the current one.

        Marks all existing concepts as not current and sets
        the specified concept as current.
        """
        user = cast(User, request.user)
        if pk is None:
            return Response(
                {"error": "Concept ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project = get_current_project(user)
        if not project:
            return Response(
                {"error": "No active project found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            concept = GameConcept.objects.get(pk=pk, user=user, project=project)
        except GameConcept.DoesNotExist:
            return Response(
                {"error": "Game concept not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark all existing concepts as not current
        GameConcept.objects.filter(project=project, is_current=True).update(
            is_current=False
        )

        # Set selected concept as current
        concept.is_current = True
        concept.save()

        serializer = GameConceptSerializer(concept)
        return Response(serializer.data)


class ProjectViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self) -> QuerySet[Project]:
        user = cast(User, self.request.user)
        return Project.objects.filter(user=user).order_by("-updated_at")

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        user = cast(User, self.request.user)
        name = serializer.validated_data.get("name") or "Untitled Project"
        is_current = bool(serializer.validated_data.get("is_current"))
        if is_current:
            Project.objects.filter(user=user, is_current=True).update(is_current=False)
        elif not Project.objects.filter(user=user, is_current=True).exists():
            serializer.save(user=user, is_current=True, name=name)
            return
        serializer.save(user=user, name=name)

    @action(detail=False, methods=["get"])
    def current(self, request: Request) -> Response:
        user = cast(User, request.user)
        project = get_current_project(user)
        if not project:
            return Response(
                {"detail": "No current project found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="switch")
    def switch(self, request: Request, pk: Optional[int] = None) -> Response:
        user = cast(User, request.user)
        if pk is None:
            return Response(
                {"error": "Project ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            project = Project.objects.get(pk=pk, user=user)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        Project.objects.filter(user=user, is_current=True).update(is_current=False)
        project.is_current = True
        project.save(update_fields=["is_current"])
        return Response(ProjectSerializer(project).data)

    @action(detail=True, methods=["post"], url_path="clone")
    def clone(self, request: Request, pk: Optional[int] = None) -> Response:
        user = cast(User, request.user)
        if pk is None:
            return Response(
                {"error": "Project ID is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            source_project = Project.objects.get(pk=pk, user=user)
        except Project.DoesNotExist:
            return Response(
                {"error": "Project not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        include_concept = bool(request.data.get("include_concept", True))
        include_pillars = bool(request.data.get("include_pillars", True))
        include_charts = bool(request.data.get("include_charts", True))
        include_nodes = bool(request.data.get("include_nodes", True))

        name = request.data.get("name") or f"{source_project.name} (Copy)"
        new_project = Project.objects.create(
            user=user,
            name=name,
            description=source_project.description,
            is_current=False,
        )

        def_map: dict[str, PxComponentDefinition] = {}
        node_map: dict[str, PxNode] = {}

        if include_concept:
            concepts = GameConcept.objects.filter(project=source_project).order_by(
                "created_at"
            )
            for concept in concepts:
                GameConcept.objects.create(
                    user=user,
                    project=new_project,
                    content=concept.content,
                    is_current=concept.is_current,
                    last_sparc_evaluation=concept.last_sparc_evaluation,
                )

        if include_pillars:
            pillars = Pillar.objects.filter(project=source_project)
            for pillar in pillars:
                Pillar.objects.create(
                    user=user,
                    project=new_project,
                    name=pillar.name,
                    description=pillar.description,
                )

        if include_nodes:
            definitions = PxComponentDefinition.objects.filter(project=source_project)
            for definition in definitions:
                new_def = PxComponentDefinition.objects.create(
                    id=uuid.uuid4(),
                    name=definition.name,
                    type=definition.type,
                    owner=user,
                    project=new_project,
                )
                def_map[str(definition.id)] = new_def

            nodes = PxNode.objects.filter(project=source_project)
            for node in nodes:
                new_node = PxNode.objects.create(
                    id=uuid.uuid4(),
                    name=node.name,
                    description=node.description,
                    owner=user,
                    project=new_project,
                )
                node_map[str(node.id)] = new_node

                components = node.components.all()
                for component in components:
                    comp_def: PxComponentDefinition | None = def_map.get(
                        str(component.definition_id)
                    )
                    if not comp_def:
                        comp_def = PxComponentDefinition.objects.create(
                            id=uuid.uuid4(),
                            name=component.definition.name,
                            type=component.definition.type,
                            owner=user,
                            project=new_project,
                        )
                        def_map[str(component.definition_id)] = comp_def
                    PxComponent.objects.create(
                        id=uuid.uuid4(),
                        node=new_node,
                        definition=comp_def,
                        value=component.value,
                        owner=user,
                    )

        if include_charts:
            charts = PxChart.objects.filter(project=source_project)
            for chart in charts:
                new_associated_node = None
                if include_nodes and chart.associatedNode:
                    new_associated_node = node_map.get(str(chart.associatedNode_id))

                new_chart = PxChart.objects.create(
                    id=uuid.uuid4(),
                    name=chart.name,
                    description=chart.description,
                    project=new_project,
                    associatedNode=new_associated_node,
                    owner=user,
                )

                container_map: dict[str, PxChartContainer] = {}
                for container in chart.containers.all():
                    new_content = None
                    if include_nodes and container.content_id:
                        new_content = node_map.get(str(container.content_id))
                    new_container = PxChartContainer.objects.create(
                        id=uuid.uuid4(),
                        px_chart=new_chart,
                        name=container.name,
                        content=new_content,
                        owner=user,
                    )
                    container_map[str(container.id)] = new_container

                    if hasattr(container, "layout") and container.layout:
                        layout = getattr(new_container, "layout", None)
                        if layout:
                            layout.position_x = container.layout.position_x
                            layout.position_y = container.layout.position_y
                            layout.height = container.layout.height
                            layout.width = container.layout.width
                            layout.save(
                                update_fields=[
                                    "position_x",
                                    "position_y",
                                    "height",
                                    "width",
                                ]
                            )
                        else:
                            PxChartContainerLayout.objects.create(
                                container=new_container,
                                position_x=container.layout.position_x,
                                position_y=container.layout.position_y,
                                height=container.layout.height,
                                width=container.layout.width,
                            )

                for edge in chart.edges.all():
                    new_source = container_map.get(str(edge.source_id))
                    new_target = container_map.get(str(edge.target_id))
                    PxChartEdge.objects.create(
                        id=uuid.uuid4(),
                        px_chart=new_chart,
                        source=new_source,
                        sourceHandle=edge.sourceHandle,
                        target=new_target,
                        targetHandle=edge.targetHandle,
                        owner=user,
                    )

        return Response(
            ProjectSerializer(new_project).data, status=status.HTTP_201_CREATED
        )
