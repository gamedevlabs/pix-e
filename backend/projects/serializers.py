from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "genres",
            "target_platforms",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_genres(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Genres must be a list.")

        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Each genre must be a string.")

        return value