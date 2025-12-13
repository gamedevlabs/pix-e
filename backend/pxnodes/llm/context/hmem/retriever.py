"""
H-MEM Retriever with Positional Index Routing.

Implements vector similarity retrieval with hierarchical layer routing
from Sun & Zeng (2025) "H-MEM: Hierarchical Memory for High-Efficiency
Long-Term Reasoning in LLM Agents".

Key features:
- Vector embeddings for semantic similarity
- Positional index encoding for layer routing
- Top-down retrieval (L1 -> L4) for context building
"""

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
from pxnodes.models import HMEMLayerEmbedding

logger = logging.getLogger(__name__)


@dataclass
class HMEMRetrievalResult:
    """Result of H-MEM retrieval for a single layer."""

    layer: int
    layer_name: str
    content: str
    positional_index: str
    similarity_score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HMEMContextResult:
    """Complete H-MEM retrieval result across all layers."""

    query: str
    results_by_layer: dict[int, list[HMEMRetrievalResult]] = field(default_factory=dict)
    total_retrieved: int = 0

    def get_layer(self, layer: int) -> list[HMEMRetrievalResult]:
        """Get results for a specific layer."""
        return self.results_by_layer.get(layer, [])

    def get_best_per_layer(self) -> dict[int, Optional[HMEMRetrievalResult]]:
        """Get the best (highest similarity) result per layer."""
        return {
            layer: results[0] if results else None
            for layer, results in self.results_by_layer.items()
        }


LAYER_NAMES = {
    1: "Domain",
    2: "Category",
    3: "Trace",
    4: "Episode",
}


class HMEMRetriever:
    """
    Retriever for H-MEM hierarchical memory with vector similarity.

    Uses positional index routing to filter by layer and scope,
    then vector similarity to rank results within that scope.
    """

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-small",
        embedding_dim: int = 1536,
    ):
        """
        Initialize the H-MEM retriever.

        Args:
            embedding_model: OpenAI embedding model name
            embedding_dim: Dimension of embeddings
        """
        self.embedding_generator = OpenAIEmbeddingGenerator(model=embedding_model)
        self.embedding_model = embedding_model
        self.embedding_dim = embedding_dim

    def retrieve(
        self,
        query: str,
        project_id: str = "default",
        chart_id: Optional[str] = None,
        node_id: Optional[str] = None,
        top_k_per_layer: int = 3,
        layers: Optional[list[int]] = None,
    ) -> HMEMContextResult:
        """
        Retrieve context from H-MEM using vector similarity.

        Performs top-down retrieval starting from L1 (Domain) down to
        L4 (Episode), using positional index routing to filter scope.

        Args:
            query: Query text to embed and search
            project_id: Project ID for routing (L1+)
            chart_id: Chart ID for routing (L2+)
            node_id: Node ID for routing (L4)
            top_k_per_layer: Number of results per layer
            layers: Specific layers to retrieve (default all)

        Returns:
            HMEMContextResult with results organized by layer
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Default to all layers
        if layers is None:
            layers = [1, 2, 3, 4]

        result = HMEMContextResult(query=query)

        for layer in layers:
            # Build positional index filter pattern
            index_pattern = self._build_index_pattern(
                layer, project_id, chart_id, node_id
            )

            # Retrieve from this layer
            layer_results = self._retrieve_layer(
                query_embedding=query_embedding,
                layer=layer,
                index_pattern=index_pattern,
                top_k=top_k_per_layer,
            )

            result.results_by_layer[layer] = layer_results
            result.total_retrieved += len(layer_results)

        return result

    def store_embedding(
        self,
        content: str,
        layer: int,
        project_id: str = "default",
        chart_id: str = "",
        path_hash: str = "",
        node_id: str = "",
        node: Optional[Any] = None,
        chart: Optional[Any] = None,
    ) -> HMEMLayerEmbedding:
        """
        Store a new layer embedding in the H-MEM database.

        Args:
            content: Text content to embed
            layer: Layer level (1-4)
            project_id: Project identifier
            chart_id: Chart identifier
            path_hash: Hash of the path (for L3)
            node_id: Node identifier (for L4)
            node: Optional PxNode instance
            chart: Optional PxChart instance

        Returns:
            Created HMEMLayerEmbedding instance
        """
        # Build positional index
        positional_index = HMEMLayerEmbedding.build_positional_index(
            layer=layer,
            project_id=project_id,
            chart_id=chart_id,
            path_hash=path_hash,
            node_id=node_id,
        )

        # Compute content hash for change detection
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:64]

        # Check if we already have this exact content
        existing = HMEMLayerEmbedding.objects.filter(
            positional_index=positional_index,
            content_hash=content_hash,
        ).first()

        if existing:
            logger.debug(f"Reusing existing embedding: {positional_index}")
            return existing

        # Generate embedding
        embedding = self.embedding_generator.generate_embedding(content)

        # Store in database
        instance, created = HMEMLayerEmbedding.objects.update_or_create(
            positional_index=positional_index,
            defaults={
                "layer": layer,
                "content": content,
                "embedding": embedding,
                "embedding_model": self.embedding_model,
                "embedding_dim": self.embedding_dim,
                "content_hash": content_hash,
                "node": node,
                "chart": chart,
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} H-MEM embedding: {positional_index}")

        return instance

    def _retrieve_layer(
        self,
        query_embedding: list[float],
        layer: int,
        index_pattern: str,
        top_k: int,
    ) -> list[HMEMRetrievalResult]:
        """Retrieve embeddings for a specific layer with filtering."""
        # Query database with positional index prefix filter
        candidates = HMEMLayerEmbedding.objects.filter(
            layer=layer,
            positional_index__startswith=index_pattern,
        )

        # Calculate similarities
        results = []
        query_np = np.array(query_embedding)

        for candidate in candidates:
            candidate_embedding = np.array(candidate.embedding)
            similarity = self._cosine_similarity(query_np, candidate_embedding)

            results.append(
                HMEMRetrievalResult(
                    layer=layer,
                    layer_name=LAYER_NAMES.get(layer, f"L{layer}"),
                    content=candidate.content,
                    positional_index=candidate.positional_index,
                    similarity_score=float(similarity),
                    metadata={
                        "id": candidate.id,
                        "node_id": str(candidate.node_id) if candidate.node else None,
                        "chart_id": (
                            str(candidate.chart_id) if candidate.chart else None
                        ),
                        "created_at": candidate.created_at.isoformat(),
                    },
                )
            )

        # Sort by similarity (descending) and take top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]

    def _build_index_pattern(
        self,
        layer: int,
        project_id: str,
        chart_id: Optional[str],
        node_id: Optional[str],
    ) -> str:
        """Build positional index prefix pattern for filtering."""
        # Always include layer and project
        pattern = f"L{layer}.{project_id}"

        # Add chart if available and relevant
        if chart_id and layer >= 2:
            pattern += f".{chart_id}"
        elif layer >= 2:
            # Wildcard - match any chart at this level
            pattern += "."

        return pattern

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)


def compute_path_hash(path_nodes: list[Any]) -> str:
    """Compute a hash for a path of nodes."""
    path_ids = [str(getattr(n, "id", n)) for n in path_nodes]
    path_str = "->".join(path_ids)
    return hashlib.md5(path_str.encode()).hexdigest()[:12]
