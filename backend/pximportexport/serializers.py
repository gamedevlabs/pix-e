from rest_framework import serializers

from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode


class PxNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxNode
        fields = ["id", "name", "description"]


class PxComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponent
        fields = ["id", "node", "definition", "value"]


class PxComponentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponentDefinition
        fields = ["id", "name", "type"]


class PxChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChart
        fields = ["id", "name", "description", "associatedNode"]


class PxChartContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartContainer
        fields = ["id", "px_chart", "name", "content"]


class PxChartContainerLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartContainerLayout
        fields = ["id", "container", "position_x", "position_y", "height", "width"]


class PxChartEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartEdge
        fields = ["id", "px_chart", "source", "sourceHandle", "target", "targetHandle"]
