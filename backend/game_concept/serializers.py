"""
Serializers for the game_concept app.
"""

from rest_framework import serializers

from .models import GameConcept, Project
from .utils import get_current_project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GameConceptSerializer(serializers.ModelSerializer):
    """
    Serializer for GameConcept model.
    Includes all fields and read-only computed fields.
    """

    user: serializers.StringRelatedField = serializers.StringRelatedField(
        read_only=True
    )
    last_sparc_evaluation_id: serializers.PrimaryKeyRelatedField = (
        serializers.PrimaryKeyRelatedField(
            source="last_sparc_evaluation", read_only=True
        )
    )

    class Meta:
        model = GameConcept
        fields = [
            "id",
            "user",
            "project",
            "content",
            "is_current",
            "last_sparc_evaluation_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "project", "created_at", "updated_at"]


class GameConceptListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for list views.
    Shows preview of content instead of full text.
    """

    user: serializers.StringRelatedField = serializers.StringRelatedField(
        read_only=True
    )
    content_preview: serializers.SerializerMethodField = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = GameConcept
        fields = [
            "id",
            "user",
            "project",
            "content_preview",
            "is_current",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "project", "created_at", "updated_at"]

    def get_content_preview(self, obj: GameConcept) -> str:
        """Return preview of content (first 100 characters)."""
        if len(obj.content) > 100:
            return obj.content[:100] + "..."
        return obj.content


class GameConceptCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating game concepts.
    Automatically sets user from request context.
    """

    class Meta:
        model = GameConcept
        fields = ["content"]

    def create(self, validated_data):
        """
        Create a new game concept.
        Automatically marks previous concepts as not current.
        """
        user = self.context["request"].user
        project = get_current_project(user)
        if not project:
            project = Project.objects.create(user=user, name="Untitled Project")

        # Mark all existing concepts as not current
        GameConcept.objects.filter(project=project, is_current=True).update(
            is_current=False
        )

        # Create new current concept
        return GameConcept.objects.create(
            user=user, project=project, is_current=True, **validated_data
        )
