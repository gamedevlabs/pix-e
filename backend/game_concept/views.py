"""
Views for the game_concept app.
"""

from typing import Any, Optional, Type, cast

from django.contrib.auth.models import User
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from .models import GameConcept, Project
from .serializers import (
    GameConceptCreateSerializer,
    GameConceptListSerializer,
    GameConceptSerializer,
    ProjectSerializer,
)
from .services import clone_project
from .utils import get_current_game_concept, get_current_project


class GameConceptViewSet(ModelViewSet):
    """ViewSet for managing game concepts."""

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
        """Get the current game concept for the user."""
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
        """Get all game concepts for the active project."""
        user = cast(User, request.user)
        project = get_current_project(user)
        if not project:
            return Response([], status=status.HTTP_200_OK)
        concepts = GameConcept.objects.filter(project=project).order_by("-updated_at")

        serializer = GameConceptSerializer(concepts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def update_current(self, request: Request) -> Response:
        """Update or create the current game concept."""
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
        """Restore a past game concept as the current one."""
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
        new_project = clone_project(
            source_project=source_project,
            user=user,
            name=name,
            include_concept=include_concept,
            include_pillars=include_pillars,
            include_charts=include_charts,
            include_nodes=include_nodes,
        )
        return Response(
            ProjectSerializer(new_project).data, status=status.HTTP_201_CREATED
        )
