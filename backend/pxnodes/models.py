from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


# Create your models here.
class PxNode(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class PxComponentDefinition(models.Model):
    TYPE_CHOICES = [("number", "Number"), ("string", "String"), ("boolean", "Boolean")]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.type})"


class PxComponent(models.Model):
    node = models.ForeignKey(
        "PxNode", on_delete=models.CASCADE, related_name="components"
    )
    definition = models.ForeignKey("PxComponentDefinition", on_delete=models.CASCADE)
    value = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.node.name} - {self.definition.name}: ({self.value})"
