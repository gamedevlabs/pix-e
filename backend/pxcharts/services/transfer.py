from pxcharts.models import PxChart, PxChartContainer, PxChartContainerLayout, PxChartEdge, PxLockAssignment
from pxcharts.transfer_serializers import PxChartTransferSerializer, PxChartContainerSerializer, PxChartContainerLayoutSerializer, \
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
        "px_charts": PxChartTransferSerializer(pxcharts, many=True).data,
        "px_chart_containers": PxChartContainerSerializer(
            pxchartcontainers, many=True
        ).data,
        "px_chart_container_layouts": PxChartContainerLayoutSerializer(
            pxchartcontainerlayouts, many=True
        ).data,
        "px_chart_edges": PxChartEdgeSerializer(pxchartedges, many=True).data,
        "lock_assignments": PxLockAssignmentSerializer(pxLockAssignments, many=True).data,
    }

def import_project_data(project, payload, user):
    px_charts = payload.get("px_charts", [])

    chart_map = {}
    for chart_data in px_charts:
        old_id = chart_data["id"]

        chart = PxChart.objects.create(
            project=project,
            owner=user,
            name=chart_data["name"],
            description=chart_data["description"],
        )

        chart_map[old_id] = chart

    px_chart_containers = payload.get("px_chart_containers", [])

    container_map = {}
    for container_data in px_chart_containers:
        old_id = container_data["id"]

        container = PxChartContainer.objects.create(
            project=project,
            owner=user,
            name=container_data["name"],
            px_chart=chart_map[container_data["px_chart"]],
        )

        container_map[old_id] = container

    return project