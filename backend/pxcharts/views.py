from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from pxcharts.models import PxChart, PxChartEdge, PxChartNode
from pxcharts.permissions import IsOwner
from pxcharts.serializers import (
    PxChartDetailSerializer,
    PxChartEdgeSerializer,
    PxChartNodeDetailSerializer,
    PxChartNodeSerializer,
    PxChartSerializer,
)


class PxChartViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        if self.action == "list":
            return PxChart.objects.filter(owner=self.request.user).prefetch_related(
                "nodes", "edges"
            )
        return PxChart.objects.order_by("created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxChartDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PxChartNodeViewSet(viewsets.ModelViewSet):
    serializer_class = PxChartNodeSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_serializer_class(self):
        if (
            self.action == "retrieve"
            or self.action == "update"
            or self.action == "partial_update"
        ):
            return PxChartNodeDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "list":
            return PxChartNode.objects.filter(
                px_chart_id=self.kwargs["px_chart_pk"],
                px_chart__owner=self.request.user,
                owner=self.request.user,
            )
        return PxChartNode.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(px_chart_id=self.kwargs["px_chart_pk"], owner=self.request.user)


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
        serializer.save(px_chart_id=chart_id, owner=self.request.user)
