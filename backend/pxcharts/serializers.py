from rest_framework import serializers

from .models import PxChart, PxChartEdge, PxChartNode


class PxChartNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartNode
        fields = [
            "id",
            "name",
            "content",
            "position_x",
            "position_y",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class PxChartNodeFlowSerializer(serializers.ModelSerializer):
    position = serializers.SerializerMethodField()

    class Meta:
        model = PxChartNode
        fields = ["id", "position", "content"]

    def get_position(self, obj):
        return {"x": obj.position_x, "y": obj.position_y}


class PxChartEdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartEdge
        fields = ["id", "source", "target", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        chart_id = self.context["view"].kwargs.get("px_chart_pk")

        if data["source"].px_chart_id != int(chart_id):
            raise serializers.ValidationError(
                "Source node does not belong to the chart."
            )
        if data["target"].px_chart_id != int(chart_id):
            raise serializers.ValidationError(
                "Target node does not belong to the chart."
            )
        return data


class PxChartDetailSerializer(serializers.ModelSerializer):
    nodes = PxChartNodeSerializer(many=True, read_only=True)
    edges = PxChartEdgeSerializer(many=True, read_only=True)

    class Meta:
        model = PxChart
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "created_at",
            "updated_at",
            "nodes",
            "edges",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class PxChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChart
        fields = ["id", "name", "description", "owner", "created_at", "updated_at"]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
