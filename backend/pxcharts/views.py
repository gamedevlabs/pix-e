import uuid

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from pxcharts.models import PxChart, PxChartContainer, PxChartEdge
from pxcharts.permissions import IsOwner
from pxcharts.serializers import (
    PxChartContainerDetailSerializer,
    PxChartContainerSerializer,
    PxChartDetailSerializer,
    PxChartEdgeSerializer,
    PxChartSerializer,
)


class PxChartViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        if self.action == "list":
            return PxChart.objects.filter(owner=self.request.user).prefetch_related(
                "containers", "edges"
            )
        return PxChart.objects.order_by("created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxChartDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(id=uuid.uuid4(), owner=self.request.user)


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
        if self.action == "list":
            return PxChartContainer.objects.filter(
                px_chart_id=self.kwargs["px_chart_pk"],
                px_chart__owner=self.request.user,
                owner=self.request.user,
            )
        return PxChartContainer.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(id=uuid.uuid4(), px_chart_id=self.kwargs["px_chart_pk"], owner=self.request.user)


class PxChartEdgeViewSet(viewsets.ModelViewSet):
    queryset = PxChartEdge.objects.all()
    serializer_class = PxChartEdgeSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        if self.action == "list":
            chart_id = self.kwargs["px_chart_pk"]
            return PxChartEdge.objects.filter(
                px_chart_id=chart_id,
                px_chart__owner=self.request.user,
                owner=self.request.user,
            )
        return PxChartEdge.objects.order_by("created_at")

    def perform_create(self, serializer):
        chart_id = self.kwargs["px_chart_pk"]
        serializer.save(id=uuid.uuid4(), px_chart_id=chart_id, owner=self.request.user)
