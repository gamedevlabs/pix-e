from rest_framework import serializers

from pxnodes.models import PxNode

from .models import PxChart, PxChartEdge, PxChartNode, PxChartNodeLayout


class PxChartNodeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    content = serializers.PrimaryKeyRelatedField(
        queryset=PxNode.objects.all(), allow_null=True, required=False
    )

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
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxChartNodeLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartNodeLayout
        fields = ["id", "position_x", "position_y", "width", "height"]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxChartNodeDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)
    layout = PxChartNodeLayoutSerializer()
    content = serializers.PrimaryKeyRelatedField(
        queryset=PxNode.objects.all(), allow_null=True, required=False
    )

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
        read_only_fields = ["owner", "created_at", "updated_at", "px_chart"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )

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
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxChartEdge
        fields = ["id", "source", "target", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

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

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxChartDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)
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
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxChartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxChart
        fields = ["id", "name", "description", "owner", "created_at", "updated_at"]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)
