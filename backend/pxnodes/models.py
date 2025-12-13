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


class HMEMLayerEmbedding(models.Model):
    """
    Stores embeddings for H-MEM hierarchical memory layers.

    Based on Sun & Zeng (2025) "H-MEM: Hierarchical Memory for
    High-Efficiency Long-Term Reasoning in LLM Agents".

    Uses positional index encoding for routing:
    - Format: L{layer}.{project}.{chart}.{path_hash}.{node}
    - Example: L4.proj1.chart1.abc123.node1

    Layers:
    - L1 (Domain): Project-level context (Pillars, Game Concept)
    - L2 (Category): Chart-level context
    - L3 (Trace): Path/sequence context
    - L4 (Episode): Node-level context
    """

    LAYER_CHOICES = [
        (1, "L1 - Domain (Project)"),
        (2, "L2 - Category (Chart)"),
        (3, "L3 - Trace (Path)"),
        (4, "L4 - Episode (Node)"),
    ]

    # Positional index for routing (unique identifier)
    positional_index = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Format: L{layer}.{project}.{chart}.{path}.{node}",
    )

    # Layer level (1-4)
    layer = models.IntegerField(choices=LAYER_CHOICES, db_index=True)

    # Content that was embedded
    content = models.TextField()

    # The embedding vector (stored as JSON array)
    embedding = models.JSONField(help_text="Vector embedding as JSON array of floats")

    # Embedding model used
    embedding_model = models.CharField(
        max_length=100,
        default="text-embedding-3-small",
    )

    # Dimension of the embedding
    embedding_dim = models.IntegerField(default=1536)

    # Foreign keys to related objects (optional, for easier lookups)
    node = models.ForeignKey(
        "PxNode",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hmem_embeddings",
    )
    chart = models.ForeignKey(
        "pxcharts.PxChart",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hmem_embeddings",
    )

    # Content hash for change detection
    content_hash = models.CharField(max_length=64, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["layer", "chart"]),
            models.Index(fields=["layer", "node"]),
            models.Index(fields=["positional_index"]),
            models.Index(fields=["content_hash"]),
        ]

    def __str__(self):
        return f"HMEMEmbedding(L{self.layer}, {self.positional_index})"

    @classmethod
    def build_positional_index(
        cls,
        layer: int,
        project_id: str = "default",
        chart_id: str = "",
        path_hash: str = "",
        node_id: str = "",
    ) -> str:
        """
        Build a positional index string for routing.

        Format: L{layer}.{project}.{chart}.{path_hash}.{node}
        """
        parts = [f"L{layer}", project_id]

        if chart_id:
            parts.append(chart_id)
        else:
            parts.append("_")

        if path_hash:
            parts.append(path_hash)
        else:
            parts.append("_")

        if node_id:
            parts.append(node_id)
        else:
            parts.append("_")

        return ".".join(parts)

    @classmethod
    def parse_positional_index(cls, index: str) -> dict:
        """Parse a positional index into its components."""
        parts = index.split(".")

        result = {
            "layer": int(parts[0][1]) if parts else 0,
            "project_id": parts[1] if len(parts) > 1 and parts[1] != "_" else None,
            "chart_id": parts[2] if len(parts) > 2 and parts[2] != "_" else None,
            "path_hash": parts[3] if len(parts) > 3 and parts[3] != "_" else None,
            "node_id": parts[4] if len(parts) > 4 and parts[4] != "_" else None,
        }

        return result
