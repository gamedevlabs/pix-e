from rest_framework import serializers

from .models import PxComponent, PxComponentDefinition, PxNode


class PxNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxNode
        fields = "__all__"
        read_only_fields = ["owner", "created_at", "updated_at"]


class PxComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponent
        fields = "__all__"


class PxComponentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PxComponentDefinition
        fields = "__all__"
