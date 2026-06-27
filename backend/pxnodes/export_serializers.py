from rest_framework import serializers

from pxcharts.serializers import PxChartSerializer

from .models import (
    PxComponent,
    PxComponentDefinition,
    PxKeyAssignment,
    PxKeyDefinition,
    PxLockDefinition,
    PxNode,
)


class PxNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxNode
        fields = [
            "id",
            "name",
            "description",
        ]


class PxComponentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponentDefinition
        fields = [
            "id",
            "name",
            "type",
        ]


class PxComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponent
        fields = [
            "id",
            "node",
            "definition",
            "value",
        ]


class PxKeyDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxKeyDefinition
        fields = ["id", "name", "key_type", "consumable", "fixed", "unique"]


class PxKeyAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxKeyAssignment
        fields = ["id", "node", "definition", "count"]


class PxLockDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxLockDefinition
        fields = ["id", "name", "unlocked_by", "soft_gate", "unlock_mode"]
