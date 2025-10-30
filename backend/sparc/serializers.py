"""Serializers for SPARC API endpoints."""

from rest_framework import serializers

from sparc.models import SPARCEvaluation, SPARCEvaluationResult


class SPARCEvaluationResultSerializer(serializers.ModelSerializer):
    """Serializer for individual aspect results."""

    class Meta:
        model = SPARCEvaluationResult
        fields = [
            "id",
            "aspect",
            "score",
            "agent_name",
            "model_used",
            "execution_time_ms",
            "result_data",
            "created_at",
        ]


class SPARCEvaluationSerializer(serializers.ModelSerializer):
    """Serializer for SPARC evaluations with nested aspect results."""

    aspect_results = SPARCEvaluationResultSerializer(many=True, read_only=True)

    class Meta:
        model = SPARCEvaluation
        fields = [
            "id",
            "game_text",
            "context",
            "mode",
            "model_id",
            "execution_time_ms",
            "total_tokens",
            "estimated_cost_eur",
            "aspect_results",
            "created_at",
            "updated_at",
        ]
