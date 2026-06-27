from pxcharts.models import PxChart, PxChartContainer, PxChartContainerLayout, PxChartEdge, PxLockAssignment
from pxcharts.export_serializers import PxChartSerializer, PxChartContainerSerializer, PxChartContainerLayoutSerializer, \
    PxChartEdgeSerializer, PxLockAssignmentSerializer


def export_project_data(project):
    pxcharts = PxChart.objects.filter(project=project)

    pxchartcontainers = PxChartContainer.objects.filter(px_chart__in=pxcharts)
    pxchartcontainerlayouts = PxChartContainerLayout.objects.filter(
        container__in=pxchartcontainers
    )
    pxchartedges = PxChartEdge.objects.filter(px_chart__in=pxcharts)

    pxLockAssignments = PxLockAssignment.objects.filter(px_chart__in=pxcharts)

    return {
        "px_charts": PxChartSerializer(pxcharts, many=True).data,
        "px_chart_containers": PxChartContainerSerializer(
            pxchartcontainers, many=True
        ).data,
        "px_chart_container_layouts": PxChartContainerLayoutSerializer(
            pxchartcontainerlayouts, many=True
        ).data,
        "px_chart_edges": PxChartEdgeSerializer(pxchartedges, many=True).data,
        "lock_assignments": PxLockAssignmentSerializer(pxLockAssignments, many=True).data,
    }