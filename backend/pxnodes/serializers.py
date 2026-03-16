from rest_framework import serializers

from pxcharts.serializers import PxChartSerializer

from .models import PxComponent, PxComponentDefinition, PxNode, PxKeyDefinition, PxKeyAssignment, PxLockDefinition


class PxComponentSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = PxComponentDefinition
        fields = "__all__"
        read_only_fields = ["project"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxNode
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "project",
            "updated_at",
            "created_at",
        ]
        read_only_fields = ["owner", "project", "created_at", "updated_at"]

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
            "project",
            "updated_at",
            "created_at",
        ]
        read_only_fields = ["owner", "project", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxKeyDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxKeyDefinition
        fields = "__all__"

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxKeyAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxKeyAssignment
        fields = "__all__"

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)


class PxLockDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxLockDefinition
        fields = "__all__"

    def update(self, instance, validated_data):
        if "id" in validated_data and validated_data["id"] != instance.id:
            raise serializers.ValidationError(
                {"id": "Cannot update ID after creation."}
            )
        return super().update(instance, validated_data)

