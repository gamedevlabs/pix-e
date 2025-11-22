from django.db import models


class Pillar(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="pillars"
    )

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ID: ({self.id}), {self.name}:\n {self.description}"
