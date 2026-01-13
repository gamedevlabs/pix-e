from django.db import models


class Pillar(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="pillars"
    )
    project = models.ForeignKey(
        "game_concept.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pillars",
    )

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID: ({self.id}), {self.name}:\n {self.description}"


class PillarLLMCall(models.Model):
    """
    Tracks LLM call metrics for pillar operations.

    Records token usage, execution time, and cost for each LLM operation
    to support thesis research on LLM usage patterns.
    """

    OPERATION_CHOICES = [
        ("validate", "Validate Pillar"),
        ("improve", "Improve Pillar"),
        ("improve_explained", "Improve with Explanation"),
        ("evaluate_completeness", "Evaluate Completeness"),
        ("evaluate_contradictions", "Evaluate Contradictions"),
        ("suggest_additions", "Suggest Additions"),
        ("evaluate_context", "Evaluate Context"),
        ("evaluate_all", "Evaluate All (Aggregated)"),
        ("concept_fit", "Concept Fit Agent"),
        ("contradictions", "Contradictions Agent"),
        ("suggest_additions_agent", "Suggest Additions Agent"),
        ("contradiction_resolution", "Contradiction Resolution Agent"),
        ("resolve_contradictions", "Resolve Contradictions"),
    ]

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="pillar_llm_calls",
    )
    pillar = models.ForeignKey(
        Pillar,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_calls",
        help_text="The pillar this call relates to (if applicable)",
    )
    parent_call = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="agent_calls",
        help_text="Parent aggregated call (for agent sub-calls)",
    )

    # Operation info
    operation = models.CharField(max_length=30, choices=OPERATION_CHOICES)
    model_id = models.CharField(max_length=100)

    # Execution metrics
    execution_time_ms = models.IntegerField()

    # Token tracking
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)

    # Cost tracking (EUR)
    estimated_cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=0,
    )

    # Store input and output for debugging/analysis
    input_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Input data sent to the LLM",
    )
    result_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Output data returned by the LLM",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Pillar LLM Call"
        verbose_name_plural = "Pillar LLM Calls"

    def __str__(self):
        return f"{self.operation} - {self.model_id} ({self.total_tokens} tokens)"
