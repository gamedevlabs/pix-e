from django.db import models
from django.contrib.auth.models import User
import uuid

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
