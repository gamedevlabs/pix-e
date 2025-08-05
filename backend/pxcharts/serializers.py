from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from .models import PxChart, PxChartContainer, PxChartContainerLayout, PxChartEdge
from .utils import GENERIC_TYPE_MAP


class PxChartContainerSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    content_type = serializers.SerializerMethodField()
    content_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = PxChartContainer
        fields = [
            "id",
            "name",
            "content_type",
            "content_id",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        print("Update in PxChartContainerSerializer")
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)

    def get_content_type(self, obj):
        if not obj.content_type: return None
        return obj.content_type.model


class PxChartContainerLayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxChartContainerLayout
        fields = ["id", "position_x", "position_y", "width", "height"]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxChartContainerDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)
    layout = PxChartContainerLayoutSerializer()
    content_type = serializers.SerializerMethodField()
    content_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = PxChartContainer
        fields = [
            "id",
            "name",
            "content_type",
            "content_id",
            "layout",
            "px_chart",
            "owner",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at", "px_chart"]

    def create(self, validated_data):
        nested_data = validated_data.pop("layout", None)

        container = PxChartContainer.objects.create(**validated_data)
        print(f"Created {container}")
        PxChartContainerLayout.objects.filter(container=container).update(**nested_data)
        return container

    def update(self, instance, validated_data):
        print("Update in PxChartContainerDetailSerializer")
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )

        layout_data = validated_data.pop("layout", None)

        # Update main container fields
        for attr, value in validated_data.items():
            print(f"{attr}, {value}")
            setattr(instance, attr, value)
        instance.save()

        # Update layout if provided
        if layout_data:
            layout = instance.layout
            for attr, value in layout_data.items():
                setattr(layout, attr, value)
            layout.save()

        return instance

    def get_content_type(self, obj):
        if not obj.content_type: return None
        return obj.content_type.model


class PxChartEdgeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxChartEdge
        fields = [
            "id",
            "source",
            "sourceHandle",
            "target",
            "targetHandle",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        chart_id = self.context["view"].kwargs.get("px_chart_pk")

        if str(data["source"].px_chart_id) != chart_id:
            raise serializers.ValidationError(
                "Source container does not belong to the chart."
            )
        if str(data["target"].px_chart_id) != chart_id:
            raise serializers.ValidationError(
                "Target container does not belong to the chart."
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
    containers = PxChartContainerDetailSerializer(many=True, read_only=True)
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
            "containers",
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
