import uuid

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from projects.utils import get_current_project
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartEdge,
    PxChartPathSettings,
    PxLockAssignment,
)
from pxcharts.permissions import IsOwner
from pxcharts.serializers import (
    PxChartContainerDetailSerializer,
    PxChartContainerSerializer,
    PxChartDetailSerializer,
    PxChartEdgeSerializer,
    PxChartPathSettingsSerializer,
    PxChartSerializer,
    PxLockAssignmentSerializer,
)


class PxChartViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        project = get_current_project(self.request.user)
        queryset = PxChart.objects.filter(owner=self.request.user)
        if project:
            queryset = queryset.filter(project=project)
        else:
            queryset = queryset.filter(project__isnull=True)
        if self.action == "list":
            return queryset.prefetch_related("containers", "edges")
        return queryset.order_by("created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxChartDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        serializer.save(id=uuid.uuid4(), owner=self.request.user, project=project)


class PxChartContainerViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartContainerSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if (
            self.action == "retrieve"
            or self.action == "update"
            or self.action == "partial_update"
            or self.action == "create"
        ):
            return PxChartContainerDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        project = get_current_project(self.request.user)
        queryset = PxChartContainer.objects.filter(
            px_chart_id=self.kwargs["px_chart_pk"],
            px_chart__owner=self.request.user,
            owner=self.request.user,
        )
        if project:
            queryset = queryset.filter(px_chart__project=project)
        else:
            queryset = queryset.filter(px_chart__project__isnull=True)
        if self.action == "list":
            return queryset
        return queryset.order_by("created_at")

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        chart_filters = {"id": self.kwargs["px_chart_pk"], "owner": self.request.user}
        if project:
            chart_filters["project"] = project
        else:
            chart_filters["project__isnull"] = True
        chart = get_object_or_404(PxChart, **chart_filters)
        serializer.save(id=uuid.uuid4(), px_chart=chart, owner=self.request.user)


class PxChartEdgeViewSet(viewsets.ModelViewSet):
    queryset = PxChartEdge.objects.all()
    serializer_class = PxChartEdgeSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        project = get_current_project(self.request.user)
        chart_id = self.kwargs["px_chart_pk"]
        queryset = PxChartEdge.objects.filter(
            px_chart_id=chart_id,
            px_chart__owner=self.request.user,
            owner=self.request.user,
        )
        if project:
            queryset = queryset.filter(px_chart__project=project)
        else:
            queryset = queryset.filter(px_chart__project__isnull=True)
        if self.action == "list":
            return queryset
        return queryset.order_by("created_at")

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        chart_filters = {"id": self.kwargs["px_chart_pk"], "owner": self.request.user}
        if project:
            chart_filters["project"] = project
        else:
            chart_filters["project__isnull"] = True
        chart = get_object_or_404(PxChart, **chart_filters)
        serializer.save(id=uuid.uuid4(), px_chart=chart, owner=self.request.user)


class PxLockAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = PxLockAssignmentSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    # TODO adapt queryset
    def get_queryset(self):
        if self.action == "list":
            chart_id = self.kwargs["px_chart_pk"]
            return PxLockAssignment.objects.filter(
                px_chart_id=chart_id,
                px_chart__owner=self.request.user,
                owner=self.request.user,
            )
        return PxLockAssignment.objects.order_by("created_at")

    # TODO adapt creation
    def perform_create(self, serializer):
        chart_id = self.kwargs["px_chart_pk"]
        serializer.save(id=uuid.uuid4(), px_chart_id=chart_id, owner=self.request.user)


class PxChartPathSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartPathSettingsSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    # TODO adapt queryset
    def get_queryset(self):
        if self.action == "list":
            chart_id = self.kwargs["px_chart_pk"]
            return PxChartPathSettings.objects.filter(
                px_chart_id=chart_id,
                px_chart__owner=self.request.user,
                owner=self.request.user,
            )
        return PxChartPathSettings.objects.order_by("created_at")

    # TODO adapt creation
    def perform_create(self, serializer):
        chart_id = self.kwargs["px_chart_pk"]
        serializer.save(id=uuid.uuid4(), px_chart_id=chart_id, owner=self.request.user)
