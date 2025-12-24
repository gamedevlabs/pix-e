from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class PxNode(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    project = models.ForeignKey(
        "game_concept.GameConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pxnodes",
    )

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
    project = models.ForeignKey(
        "game_concept.GameConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pxcomponentdefinitions",
    )

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
    summary_text = models.TextField(blank=True, default="")
    trace_summary = models.TextField(blank=True, default="")

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

    Implements H-MEM's positional index with parent-child pointers:
    - v_i^(L) = [e_i^(L), p_(i-1)x, pi1, ..., piK]
    - Each entry has a parent_index (pointer to parent in layer above)
    - Each entry has child_indices (pointers to children in layer below)

    Uses positional index encoding for routing:
    - Format: L{layer}.{project}.{chart}.{path_hash}.{node}
    - Example: L4.proj1.chart1.abc123.node1

    Layers:
    - L1 (Domain): Project-level context (Pillars, Game Concept)
    - L2 (Category): Chart-level context
    - L3 (Trace): Path/sequence context (summaries, not just names)
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

    # H-MEM Hierarchical Routing Pointers (Sun & Zeng 2025)
    # parent_index: pointer to parent entry in layer above (p_(i-1)x in paper)
    parent_index = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Positional index of parent entry (for hierarchical routing)",
    )
    # child_indices: pointers to child entries in layer below
    # (pi1, ..., piK in paper)
    child_indices = models.JSONField(
        default=list,
        help_text=(
            "List of positional indices of child entries " "(for hierarchical routing)"
        ),
    )

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
            models.Index(fields=["parent_index"]),  # For hierarchical routing
        ]

    def __str__(self):
        return f"HMEMEmbedding(L{self.layer}, {self.positional_index})"

    def add_child(self, child_index: str) -> None:
        """
        Register a child entry for hierarchical routing.

        H-MEM uses parent-child pointers to enable efficient
        top-down retrieval where parent results constrain child search.
        """
        if child_index not in self.child_indices:
            self.child_indices.append(child_index)
            self.save(update_fields=["child_indices"])

    def remove_child(self, child_index: str) -> None:
        """Remove a child entry from routing pointers."""
        if child_index in self.child_indices:
            self.child_indices.remove(child_index)
            self.save(update_fields=["child_indices"])

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


class ContextArtifact(models.Model):
    """
    Stores precomputed context artifacts for strategies.

    Artifacts are chart-scoped for nodes and paths to avoid cross-chart leakage.
    """

    SCOPE_CHOICES = [
        ("node", "Node"),
        ("chart", "Chart"),
        ("path", "Path"),
        ("concept", "Game Concept"),
        ("pillar", "Pillar"),
    ]

    ARTIFACT_CHOICES = [
        ("raw_text", "Raw Text"),
        ("chunks", "Chunks"),
        ("summary", "Summary"),
        ("facts", "Atomic Facts"),
        ("triples", "Knowledge Triples"),
        ("chart_overview", "Chart Overview"),
        ("node_list", "Node List"),
        ("path_summary", "Path Summary"),
        ("path_snippet", "Path Snippet"),
        ("milestone", "Milestone"),
    ]

    scope_type = models.CharField(max_length=20, choices=SCOPE_CHOICES)
    scope_id = models.CharField(max_length=128, db_index=True)
    artifact_type = models.CharField(max_length=32, choices=ARTIFACT_CHOICES)

    node = models.ForeignKey(
        "PxNode",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="context_artifacts",
    )
    chart = models.ForeignKey(
        "pxcharts.PxChart",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="context_artifacts",
    )
    project_id = models.CharField(max_length=128, blank=True, default="")

    content = models.JSONField()
    content_hash = models.CharField(max_length=64, db_index=True)
    source_hash = models.CharField(max_length=64, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["scope_type", "artifact_type", "scope_id"]),
            models.Index(fields=["chart", "scope_type"]),
            models.Index(fields=["node", "artifact_type"]),
        ]
        unique_together = [
            ("scope_type", "scope_id", "artifact_type", "chart", "project_id")
        ]

    def __str__(self) -> str:
        return (
            f"ContextArtifact({self.scope_type}:{self.artifact_type}:{self.scope_id})"
        )


class ArtifactEmbedding(models.Model):
    """Tracks embeddings for ContextArtifact entries."""

    artifact = models.ForeignKey(
        "ContextArtifact",
        on_delete=models.CASCADE,
        related_name="embeddings",
    )
    embedding_model = models.CharField(max_length=100)
    embedding_dim = models.IntegerField()
    embedding_hash = models.CharField(max_length=64, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["artifact", "embedding_model"]),
            models.Index(fields=["embedding_hash"]),
        ]

    def __str__(self) -> str:
        return f"ArtifactEmbedding({self.embedding_model}:{self.embedding_dim})"
