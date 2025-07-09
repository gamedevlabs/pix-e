from rest_framework import serializers

from pxnodes.serializers import PxNodeSerializer

from .models import PxChart, PxChartEdge, PxChartNode, PxChartNodeLayout


class PxChartNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartNode
        fields = [
            "id",
            "name",
            "content",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class PxChartNodeLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartNodeLayout
        fields = ["id", "position_x", "position_y", "width", "height"]
        read_only_fields = ["id"]


class PxChartNodeDetailSerializer(serializers.ModelSerializer):
    layout = PxChartNodeLayoutSerializer()
    content = PxNodeSerializer()

    class Meta:
        model = PxChartNode
        fields = [
            "id",
            "name",
            "content",
            "layout",
            "px_chart",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at", "px_chart"]

    def update(self, instance, validated_data):
        layout_data = validated_data.pop("layout", None)

        # Update main node fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update layout if provided
        if layout_data:
            layout = instance.layout
            for attr, value in layout_data.items():
                setattr(layout, attr, value)
            layout.save()

        return instance


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
    nodes = PxChartNodeDetailSerializer(many=True, read_only=True)
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
