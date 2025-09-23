from rest_framework import serializers

from pxcharts.serializers import PxChartSerializer

from .models import PxComponent, PxComponentDefinition, PxNode


class PxComponentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxComponent
        fields = "__all__"

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxComponentDefinitionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxComponentDefinition
        fields = "__all__"

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxNodeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)

    class Meta:
        model = PxNode
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "updated_at",
            "created_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxNodeDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=True)
    components = PxComponentSerializer(many=True, read_only=True)
    charts = PxChartSerializer(many=True, read_only=True)

    class Meta:
        model = PxNode
        fields = [
            "id",
            "name",
            "description",
            "components",
            "charts",
            "owner",
            "updated_at",
            "created_at",
        ]
        read_only_fields = ["owner", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)
