from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PxNode(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["owner", "id"]

    def __str__(self):
        return self.name


class PxComponentDefinition(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    TYPE_CHOICES = [("number", "Number"), ("string", "String"), ("boolean", "Boolean")]
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["owner", "id"]

    def __str__(self):
        return f"{self.name} ({self.type})"


class PxComponent(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)

    node = models.ForeignKey(
        "PxNode", on_delete=models.CASCADE, related_name="components"
    )

    definition = models.ForeignKey("PxComponentDefinition", on_delete=models.CASCADE)
    value = models.JSONField()

    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["owner", "id"]

    def __str__(self):
        return f"{self.node.name} - {self.definition.name}: ({self.value})"


class StructuralMemoryState(models.Model):
    """
    Tracks the processing state of structural memory for node+chart combinations.

    Used to detect changes and skip re-processing unchanged nodes.
    Stores a content hash of node data (name, description, components, edges)
    to detect when regeneration is needed.
    """

    node = models.ForeignKey(
        "PxNode",
        on_delete=models.CASCADE,
        related_name="structural_memory_states",
    )
    chart = models.ForeignKey(
        "pxcharts.PxChart",
        on_delete=models.CASCADE,
        related_name="structural_memory_states",
    )

    # Hash of serialized content (name + description + components + edges)
    content_hash = models.CharField(max_length=64)

    # When this node+chart was last processed
    processed_at = models.DateTimeField(auto_now=True)

    # Statistics from last generation
    triples_count = models.IntegerField(default=0)
    facts_count = models.IntegerField(default=0)
    embeddings_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ["node", "chart"]
        indexes = [
            models.Index(fields=["node", "chart"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        return f"StructuralMemory({self.node.name} in {self.chart.name})"
