from rest_framework import serializers

from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
    PxLockAssignment,
)


class PxChartTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChart
        fields = [
            "id",
            "name",
            "description",
            "associatedNode",
        ]
        read_only_fields = ["id"]


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
        fields = [
            "id",
            "px_chart",
            "source",
            "sourceHandle",
            "target",
            "targetHandle",
            "bidirectional",
        ]


class PxLockAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxLockAssignment
        fields = ["id", "px_chart", "edge", "definition", "count"]
