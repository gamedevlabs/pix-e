from django.contrib.auth.models import User
from django.db import models


# Create your models here.
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

    genres = models.JSONField(default=list, blank=True)

    target_platforms = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects_project"
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_current=True),
                name="one_current_project_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username}'s project: {self.name or 'Untitled'}"
