from rest_framework import viewsets

from pxcharts.models import PxChart, PxChartEdge, PxChartNode
from pxcharts.serializers import (
    PxChartDetailSerializer,
    PxChartEdgeSerializer,
    PxChartNodeDetailSerializer,
    PxChartNodeSerializer,
    PxChartSerializer,
)


class PxChartViewSet(viewsets.ModelViewSet):
    queryset = PxChart.objects.all().prefetch_related("nodes", "edges")
    serializer_class = PxChartSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxChartDetailSerializer
        return super().get_serializer_class()


class PxChartNodeViewSet(viewsets.ModelViewSet):
    queryset = PxChartNode.objects.all()
    serializer_class = PxChartNodeSerializer

    def get_serializer_class(self):
        if (
            self.action == "retrieve"
            or self.action == "update"
            or self.action == "partial_update"
        ):
            return PxChartNodeDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        return PxChartNode.objects.filter(px_chart_id=self.kwargs["px_chart_pk"])

    def perform_create(self, serializer):
        serializer.save(px_chart_id=self.kwargs["px_chart_pk"])


class PxChartEdgeViewSet(viewsets.ModelViewSet):
    queryset = PxChartEdge.objects.all()
    serializer_class = PxChartEdgeSerializer

    def get_queryset(self):
        chart_id = self.kwargs["px_chart_pk"]
        return PxChartEdge.objects.filter(px_chart_id=chart_id)

    def perform_create(self, serializer):
        chart_id = self.kwargs["px_chart_pk"]
        serializer.save(px_chart_id=chart_id)
