"""
Game concept models for persisting early game ideas and linking to SPARC evaluations.
"""

from django.contrib.auth.models import User
from django.db import models


class Project(models.Model):
    """
    Represents a project that groups a game concept, pillars, charts, and nodes.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="projects")
    name = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_current = models.BooleanField(
        default=False, help_text="Whether this is the user's current project"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_current=True),
                name="one_current_project_per_user",
            )
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"{self.user.username}'s project: {self.name or 'Untitled'}"


class GameConcept(models.Model):
    """
    Represents a user's game concept/idea.

    A project can have multiple game concepts over time (history), but only one
    is marked as current at any given time.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="game_concepts",
    )
    content = models.TextField(help_text="The game idea text")
    is_current = models.BooleanField(
        default=True, help_text="Whether this is the project's current game concept"
    )
    last_sparc_evaluation = models.ForeignKey(
        "sparc.SPARCEvaluation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to the most recent SPARC evaluation for this concept",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=models.Q(is_current=True),
                name="one_current_concept_per_project",
            )
        ]
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        """Return string representation of the game concept."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.user.username}'s concept: {preview}"
