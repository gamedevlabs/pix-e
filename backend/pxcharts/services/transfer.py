from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
    PxLockAssignment,
)
from pxcharts.transfer_serializers import (
    PxChartContainerLayoutSerializer,
    PxChartContainerSerializer,
    PxChartEdgeSerializer,
    PxChartTransferSerializer,
    PxLockAssignmentSerializer,
)
from services.transfer import import_objects


def export_project_data(project):
    # Every collection is ordered so that two exports of an unchanged project are
    # byte-identical on any database backend, not just wherever the query planner
    # happens to be stable. Layouts order by container, their own id being local.
    pxcharts = PxChart.objects.filter(project=project).order_by("id")

    pxchartcontainers = PxChartContainer.objects.filter(
        px_chart__in=pxcharts
    ).order_by("id")
    pxchartcontainerlayouts = PxChartContainerLayout.objects.filter(
        container__in=pxchartcontainers
    ).order_by("container_id")
    pxchartedges = PxChartEdge.objects.filter(px_chart__in=pxcharts).order_by("id")

    pxLockAssignments = PxLockAssignment.objects.filter(px_chart__in=pxcharts).order_by(
        "id"
    )

    return {
        "px_charts": PxChartTransferSerializer(pxcharts, many=True).data,
        "px_chart_containers": PxChartContainerSerializer(
            pxchartcontainers, many=True
        ).data,
        "px_chart_container_layouts": PxChartContainerLayoutSerializer(
            pxchartcontainerlayouts, many=True
        ).data,
        "px_chart_edges": PxChartEdgeSerializer(pxchartedges, many=True).data,
        "px_lock_assignments": PxLockAssignmentSerializer(
            pxLockAssignments, many=True
        ).data,
    }


def import_project_data(project, payload, user, node_map, lock_definition_map):
    chart_map = import_objects(
        payload.get("px_charts", []),
        lambda d: PxChart.objects.create(
            name=d["name"],
            description=d["description"],
            associatedNode=node_map.get(d["associatedNode"]),
            project=project,
            owner=user,
        ),
    )

    container_map = import_objects(
        payload.get("px_chart_containers", []),
        lambda d: PxChartContainer.objects.create(
            name=d["name"],
            px_chart=chart_map[d["px_chart"]],
            # An empty container is a legal vertex, so content may be null.
            content=node_map.get(d["content"]) if d["content"] else None,
            owner=user,
        ),
    )

    layout_map = {}

    for d in payload.get("px_chart_container_layouts", []):
        old_id = d["id"]
        container = container_map[d["container"]]

        layout, _created = PxChartContainerLayout.objects.update_or_create(
            container=container,
            defaults={
                "position_x": d["position_x"],
                "position_y": d["position_y"],
                "width": d["width"],
                "height": d["height"],
            },
        )

        layout_map[old_id] = layout

    edge_map = import_objects(
        payload.get("px_chart_edges", []),
        lambda d: PxChartEdge.objects.create(
            sourceHandle=d["sourceHandle"],
            targetHandle=d["targetHandle"],
            bidirectional=d["bidirectional"],
            source=container_map[d["source"]],
            target=container_map[d["target"]],
            px_chart=chart_map[d["px_chart"]],
            owner=user,
        ),
    )

    _ = import_objects(
        payload.get("px_lock_assignments", []),
        lambda d: PxLockAssignment.objects.create(
            count=d["count"],
            definition=lock_definition_map[d["definition"]],
            edge=edge_map[d["edge"]],
            px_chart=chart_map[d["px_chart"]],
            owner=user,
        ),
    )

    return chart_map
