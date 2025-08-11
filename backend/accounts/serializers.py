from django.contrib.auth.models import User
from rest_framework import serializers
from .models import AIServiceToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}


class AIServiceTokenSerializer(serializers.ModelSerializer):
    """Serializer for displaying AI service tokens (without exposing actual token)"""

    masked_token = serializers.CharField(read_only=True)
    service_display = serializers.CharField(
        source="get_service_type_display", read_only=True
    )

    class Meta:
        model = AIServiceToken
        fields = [
            "id",
            "service_type",
            "service_display",
            "masked_token",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AIServiceTokenCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating AI service tokens (includes token field)"""

    token = serializers.CharField(write_only=True)

    class Meta:
        model = AIServiceToken
        fields = ["service_type", "token", "is_active"]

    def create(self, validated_data):
        token = validated_data.pop("token")
        instance = super().create(validated_data)
        instance.set_token(token)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        token = validated_data.pop("token", None)
        instance = super().update(instance, validated_data)
        if token:
            instance.set_token(token)
            instance.save()
        return instance
