from django.db import models

# Create your models here.


class Pillar(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="pillars"
    )

    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GameDesignDescription(models.Model):
    user = models.OneToOneField(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="game_designs",
        primary_key=True,
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
