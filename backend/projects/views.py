from typing import Any, Optional, cast

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import ModelViewSet

from projects.services.clone import clone_project
from pxcharts.services.transfer import export_project_data as export_charts
from pxnodes.services.transfer import export_project_data as export_nodes

from .models import Project
from .serializers import (
    ProjectSerializer,
    ProjectTransferSerializer,
)
from .services.import_project import import_project_data
from .utils import get_current_project


# Create your views here.
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

    @action(detail=False, methods=["post"], url_path="import")
    def import_project(self, request):
        with transaction.atomic():
            project = import_project_data(
                payload=request.data,
                user=request.user,
            )

        return Response(
            {"id": project.id},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        project = self.get_object()

        serializer = ProjectTransferSerializer(project)

        data = {"version": 1, "project": serializer.data}

        data.update(export_charts(project))
        data.update(export_nodes(project))

        return Response(data)

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
