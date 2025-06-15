from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.


class Pillar(models.Model):
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="pillars"
    )
    pillar_id = models.PositiveIntegerField()

    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "pillar_id"]

    def save(self, *args, **kwargs):
        if self.pillar_id is None:
            last = Pillar.objects.filter(user=self.user).order_by("-pillar_id").first()
            self.pillar_id = (last.pillar_id + 1) if last else 0
        super().save(*args, **kwargs)


class GameDesignDescription(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="game_designs",
        primary_key=True,
    )
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class MoodboardSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

class MoodboardImage(models.Model):
    session = models.ForeignKey(MoodboardSession, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=512)  # Changed from URLField to CharField for local/media paths
    prompt = models.TextField()
    is_selected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
