"""Django admin configuration for SPARC models."""

from django.contrib import admin

from sparc.models import SPARCEvaluation, SPARCEvaluationResult


class SPARCEvaluationResultInline(admin.TabularInline):
    """Inline admin for aspect results."""

    model = SPARCEvaluationResult
    extra = 0
    readonly_fields = ["aspect", "score", "agent_name", "execution_time_ms"]
    fields = ["aspect", "score", "agent_name", "execution_time_ms"]


@admin.register(SPARCEvaluation)
class SPARCEvaluationAdmin(admin.ModelAdmin):
    """Admin interface for SPARC evaluations."""

    list_display = [
        "id",
        "mode",
        "model_id",
        "execution_time_ms",
        "total_tokens",
        "estimated_cost_eur",
        "created_at",
    ]
    list_filter = ["mode", "model_id", "created_at"]
    search_fields = ["game_text", "context"]
    readonly_fields = [
        "execution_time_ms",
        "total_tokens",
        "estimated_cost_eur",
        "created_at",
        "updated_at",
    ]
    inlines = [SPARCEvaluationResultInline]


@admin.register(SPARCEvaluationResult)
class SPARCEvaluationResultAdmin(admin.ModelAdmin):
    """Admin interface for aspect results."""

    list_display = [
        "id",
        "evaluation",
        "aspect",
        "score",
        "agent_name",
        "execution_time_ms",
        "created_at",
    ]
    list_filter = ["aspect", "evaluation__mode"]
    search_fields = ["aspect", "agent_name"]
    readonly_fields = ["created_at"]
