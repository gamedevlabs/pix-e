"""
SPARC models for storing evaluation results.

Models track evaluation history, allowing users to iterate on their
game concepts and compare versions over time.
"""

from django.db import models


class SPARCEvaluation(models.Model):
    """
    A SPARC evaluation session for a game concept.

    Tracks metadata about the evaluation: when it ran, what mode was used,
    which model performed the evaluation, etc.
    """

    game_text = models.TextField(help_text="The game concept text being evaluated")
    context = models.TextField(
        blank=True, default="", help_text="Additional context or constraints"
    )
    mode = models.CharField(
        max_length=20,
        choices=[
            ("monolithic", "Monolithic"),
            ("quick_scan", "Quick Scan (Agentic)"),
            ("deep_dive", "Deep Dive (Agentic)"),
            ("interactive", "Interactive (Agentic)"),
        ],
        help_text="Execution mode used for evaluation",
    )
    model_id = models.CharField(
        max_length=100, help_text="LLM model used for evaluation"
    )
    execution_time_ms = models.IntegerField(
        help_text="Total execution time in milliseconds"
    )
    total_tokens = models.IntegerField(
        default=0, help_text="Total tokens used (prompt + completion)"
    )
    estimated_cost_eur = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=0,
        help_text="Estimated cost in EUR",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "SPARC Evaluation"
        verbose_name_plural = "SPARC Evaluations"

    def __str__(self) -> str:
        """String representation."""
        return f"SPARC Evaluation {self.id} ({self.mode}) - {self.created_at}"


class SPARCEvaluationResult(models.Model):
    """
    Results for a specific aspect within a SPARC evaluation.

    Each evaluation produces results for multiple aspects (Player Experience,
    Theme, Gameplay, etc.). This model stores the detailed results per aspect.
    """

    evaluation = models.ForeignKey(
        SPARCEvaluation,
        on_delete=models.CASCADE,
        related_name="aspect_results",
        help_text="The parent evaluation session",
    )
    aspect = models.CharField(
        max_length=50,
        choices=[
            ("player_experience", "Player Experience"),
            ("theme", "Theme"),
            ("gameplay", "Gameplay"),
            ("place", "Place"),
            ("unique_features", "Unique Features"),
            ("story_narrative", "Story & Narrative"),
            ("goals_challenges_rewards", "Goals, Challenges & Rewards"),
            ("art_direction", "Art Direction"),
            ("purpose", "Purpose"),
            ("opportunities_risks", "Opportunities & Risks"),
        ],
        help_text="Which SPARC aspect this result covers",
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Completeness score (0-100) for this aspect",
    )
    agent_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Name of agent that produced this result (for agentic mode)",
    )
    model_used = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Model used for this specific aspect",
    )
    execution_time_ms = models.IntegerField(
        null=True, blank=True, help_text="Execution time for this aspect in ms"
    )
    result_data = models.JSONField(
        help_text="Full evaluation result as JSON (structured output from LLM)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["aspect"]
        verbose_name = "SPARC Aspect Result"
        verbose_name_plural = "SPARC Aspect Results"

    def __str__(self) -> str:
        """String representation."""
        return f"{self.evaluation.id} - {self.aspect} (score: {self.score})"
