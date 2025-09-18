import uuid

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode
from pxnodes.permissions import IsOwnerPermission

from .serializers import (
    PxChartContainerLayoutSerializer,
    PxChartContainerSerializer,
    PxChartEdgeSerializer,
    PxChartSerializer,
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeSerializer,
)


class ExportDataView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get(self, request, *args, **kwargs):
        user = request.user

        pxnodes = PxNode.objects.filter(owner=user)
        pxcomponents = PxComponent.objects.filter(owner=user)
        pxcomponentdefinitions = PxComponentDefinition.objects.filter(owner=user)

        pxcharts = PxChart.objects.filter(owner=user)
        pxchartcontainers = PxChartContainer.objects.filter(owner=user)
        pxchartcontainerlayouts = PxChartContainerLayout.objects.filter(
            container__in=pxchartcontainers
        )
        pxchartedges = PxChartEdge.objects.filter(owner=user)

        data = {
            "pxnodes": PxNodeSerializer(pxnodes, many=True).data,
            "pxcomponents": PxComponentSerializer(pxcomponents, many=True).data,
            "pxcomponentdefinitions": PxComponentDefinitionSerializer(
                pxcomponentdefinitions, many=True
            ).data,
            "pxcharts": PxChartSerializer(pxcharts, many=True).data,
            "pxchartcontainers": PxChartContainerSerializer(
                pxchartcontainers, many=True
            ).data,
            "pxchartcontainerlayouts": PxChartContainerLayoutSerializer(
                pxchartcontainerlayouts, many=True
            ).data,
            "pxchartedges": PxChartEdgeSerializer(pxchartedges, many=True).data,
        }

        return Response(data)


class ImportDataView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data

        total_id_map = {}
        for componentdefinition_data in data.get("pxcomponentdefinitions", []):
            old_id = componentdefinition_data["id"]
            new_id = uuid.uuid4()
            obj, created = PxComponentDefinition.objects.update_or_create(
                id=new_id,
                owner=user,
                defaults={
                    k: v for k, v in componentdefinition_data.items() if k != "id"
                },
            )
            total_id_map[old_id] = new_id

        for node_data in data.get("pxnodes", []):
            old_id = node_data["id"]
            new_id = uuid.uuid4()
            obj, created = PxNode.objects.update_or_create(
                id=new_id,
                owner=user,
                defaults={k: v for k, v in node_data.items() if k != "id"},
            )
            total_id_map[old_id] = new_id

        for component_data in data.get("pxcomponents", []):
            old_id = component_data["id"]
            old_node_id = component_data["node"]
            old_definition_id = component_data["definition"]
            new_id = uuid.uuid4()
            obj, created = PxComponent.objects.update_or_create(
                id=new_id,
                owner=user,
                node_id=total_id_map[old_node_id],
                definition_id=total_id_map[old_definition_id],
                defaults={
                    k: v
                    for k, v in component_data.items()
                    if k != "id" and k != "node" and k != "definition"
                },
            )
            total_id_map[old_id] = new_id

        for chart_data in data.get("pxcharts", []):
            old_id = chart_data["id"]
            old_node_id = chart_data["associatedNode"]
            new_id = uuid.uuid4()
            obj, created = PxChart.objects.update_or_create(
                id=new_id,
                owner=user,
                associatedNode_id=total_id_map[old_node_id],
                defaults={
                    k: v
                    for k, v in chart_data.items()
                    if k != "id" and k != "associatedNode"
                },
            )
            total_id_map[old_id] = new_id

        for container_data in data.get("pxchartcontainers", []):
            old_id = container_data["id"]
            old_node_id = container_data["content"]
            old_px_chart_id = container_data["px_chart"]
            new_id = uuid.uuid4()
            obj, created = PxChartContainer.objects.update_or_create(
                id=new_id,
                owner=user,
                content_id=total_id_map[old_node_id],
                px_chart_id=total_id_map[old_px_chart_id],
                defaults={
                    k: v
                    for k, v in container_data.items()
                    if k not in ["id", "content", "px_chart"]
                },
            )
            total_id_map[old_id] = new_id

        for containerlayout_data in data.get("pxchartcontainerlayouts", []):
            old_id = containerlayout_data["id"]
            old_container_id = containerlayout_data["container"]
            new_id = uuid.uuid4()
            obj, created = PxChartContainerLayout.objects.update_or_create(
                container_id=total_id_map[old_container_id],
                defaults={
                    k: v
                    for k, v in containerlayout_data.items()
                    if k not in ["id", "container"]
                },
            )
            total_id_map[old_id] = new_id

        for edge_data in data.get("pxchartedges", []):
            old_id = edge_data["id"]
            old_px_chart_id = edge_data["px_chart"]
            old_source_id = edge_data["source"]
            old_target_id = edge_data["target"]
            new_id = uuid.uuid4()
            obj, created = PxChartEdge.objects.update_or_create(
                id=new_id,
                owner=user,
                px_chart_id=total_id_map[old_px_chart_id],
                source_id=total_id_map[old_source_id],
                target_id=total_id_map[old_target_id],
                defaults={
                    k: v
                    for k, v in edge_data.items()
                    if k not in ["id", "source", "target", "px_chart"]
                },
            )
            total_id_map[old_id] = new_id

        return Response({"status": "success"})
