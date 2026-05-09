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
        db_table = "projects_project"

    def __str__(self) -> str:
        return f"{self.user.username}'s project: {self.name or 'Untitled'}"
