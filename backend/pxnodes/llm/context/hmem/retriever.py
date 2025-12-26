"""
H-MEM Retriever with Hierarchical Top-Down Routing.

Implements the faithful H-MEM retrieval mechanism from Sun & Zeng (2025)
"H-MEM: Hierarchical Memory for High-Efficiency Long-Term Reasoning".

Key features (from paper):
- Vector embeddings for semantic similarity
- Positional index encoding with parent-child pointers
- **Hierarchical top-down routing**: L1 results constrain L2 search, etc.
- Formula: M_k^(l) = ⋃_{x∈M_k^(l-1)} TopK_{y∈Child(x)} (sim(q,y))

This is the key innovation of H-MEM: parent results at layer L constrain
the search space at layer L+1, enabling O((a+k·300)·D) complexity instead
of O(a·10^6·D) exhaustive search.
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
    child_indices: list[str] = field(default_factory=list)  # For routing to next layer
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HMEMContextResult:
    """Complete H-MEM retrieval result across all layers."""

    query: str
    results_by_layer: dict[int, list[HMEMRetrievalResult]] = field(default_factory=dict)
    total_retrieved: int = 0
    routing_path: list[str] = field(default_factory=list)  # Track routing decisions

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
    H-MEM Retriever with hierarchical top-down routing.

    Implements the faithful H-MEM retrieval mechanism where parent
    results constrain child search (Sun & Zeng 2025).

    The key insight: instead of searching all entries at each layer,
    we follow parent-child pointers from retrieved parents to only
    search their registered children.
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
        similarity_thresholds: Optional[dict[int, float]] = None,
        layers: Optional[list[int]] = None,
    ) -> HMEMContextResult:
        """
        Retrieve context using H-MEM hierarchical top-down routing.

        Implements the paper's key formula:
        M_k^(l) = ⋃_{x∈M_k^(l-1)} TopK_{y∈Child(x)} (sim(q,y))

        This means: for each layer, we only search among children of
        the entries retrieved at the previous layer.

        Args:
            query: Query text to embed and search
            project_id: Project ID for L1 scoping
            chart_id: Chart ID (used for fallback if routing fails)
            node_id: Node ID (used for fallback if routing fails)
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

        # H-MEM Hierarchical Top-Down Routing
        # L1 results constrain L2 search, L2 constrains L3, etc.
        parent_child_indices: Optional[list[str]] = None

        for layer in sorted(layers):
            if layer == 1:
                # L1 Domain: No parent constraint, search all L1 entries for project
                l1_results = self._retrieve_l1_domain(
                    query_embedding=query_embedding,
                    project_id=project_id,
                    top_k=top_k_per_layer,
                    similarity_threshold=(
                        similarity_thresholds.get(1) if similarity_thresholds else None
                    ),
                )
                result.results_by_layer[1] = l1_results
                result.total_retrieved += len(l1_results)

                # Extract child indices for L2 routing
                parent_child_indices = self._collect_child_indices(l1_results)
                result.routing_path.append(
                    f"L1: {len(l1_results)} hits -> "
                    f"{len(parent_child_indices)} children"
                )

            elif layer == 2:
                # L2 Category: Constrained by L1 children (if available)
                l2_results = self._retrieve_with_routing(
                    query_embedding=query_embedding,
                    layer=2,
                    parent_child_indices=parent_child_indices,
                    fallback_project_id=project_id,
                    fallback_chart_id=chart_id,
                    top_k=top_k_per_layer,
                    similarity_threshold=(
                        similarity_thresholds.get(2) if similarity_thresholds else None
                    ),
                )
                result.results_by_layer[2] = l2_results
                result.total_retrieved += len(l2_results)

                # Extract child indices for L3 routing
                parent_child_indices = self._collect_child_indices(l2_results)
                result.routing_path.append(
                    f"L2: {len(l2_results)} hits -> "
                    f"{len(parent_child_indices)} children"
                )

            elif layer == 3:
                # L3 Trace: Constrained by L2 children
                l3_results = self._retrieve_with_routing(
                    query_embedding=query_embedding,
                    layer=3,
                    parent_child_indices=parent_child_indices,
                    fallback_project_id=project_id,
                    fallback_chart_id=chart_id,
                    top_k=top_k_per_layer,
                    similarity_threshold=(
                        similarity_thresholds.get(3) if similarity_thresholds else None
                    ),
                )
                result.results_by_layer[3] = l3_results
                result.total_retrieved += len(l3_results)

                # Extract child indices for L4 routing
                parent_child_indices = self._collect_child_indices(l3_results)
                result.routing_path.append(
                    f"L3: {len(l3_results)} hits -> "
                    f"{len(parent_child_indices)} children"
                )

            elif layer == 4:
                # L4 Episode: Constrained by L3 children
                l4_results = self._retrieve_with_routing(
                    query_embedding=query_embedding,
                    layer=4,
                    parent_child_indices=parent_child_indices,
                    fallback_project_id=project_id,
                    fallback_chart_id=chart_id,
                    fallback_node_id=node_id,
                    top_k=top_k_per_layer,
                    similarity_threshold=(
                        similarity_thresholds.get(4) if similarity_thresholds else None
                    ),
                )
                result.results_by_layer[4] = l4_results
                result.total_retrieved += len(l4_results)
                result.routing_path.append(f"L4: {len(l4_results)} hits (terminal)")

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
        parent_index: Optional[str] = None,
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
            parent_index: Positional index of parent entry (for routing)

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
            # Update parent_index if it changed
            if parent_index and existing.parent_index != parent_index:
                existing.parent_index = parent_index
                existing.save(update_fields=["parent_index"])
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
                "parent_index": parent_index,
                "child_indices": [],  # Children will be added via add_child()
            },
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} H-MEM embedding: {positional_index}")

        return instance

    def _retrieve_l1_domain(
        self,
        query_embedding: list[float],
        project_id: str,
        top_k: int,
        similarity_threshold: Optional[float] = None,
    ) -> list[HMEMRetrievalResult]:
        """
        Retrieve L1 Domain entries for a project.

        L1 has no parent constraint - we search all domain-level
        entries for the given project.
        """
        candidates = HMEMLayerEmbedding.objects.filter(
            layer=1,
            positional_index__startswith=f"L1.{project_id}",
        )

        return self._rank_by_similarity(
            candidates,
            query_embedding,
            top_k,
            similarity_threshold=similarity_threshold,
        )

    def _retrieve_with_routing(
        self,
        query_embedding: list[float],
        layer: int,
        parent_child_indices: Optional[list[str]],
        fallback_project_id: str,
        fallback_chart_id: Optional[str] = None,
        fallback_node_id: Optional[str] = None,
        top_k: int = 3,
        similarity_threshold: Optional[float] = None,
    ) -> list[HMEMRetrievalResult]:
        """
        Retrieve entries using H-MEM hierarchical routing.

        If parent_child_indices is provided, we ONLY search among those
        specific entries (the children of parent hits). This is the key
        H-MEM optimization.

        If routing fails (no children), fall back to prefix-based search.
        """
        if parent_child_indices:
            # H-MEM Routing: Only search children of parent hits
            candidates = HMEMLayerEmbedding.objects.filter(
                layer=layer,
                positional_index__in=parent_child_indices,
            )

            if candidates.exists():
                logger.debug(
                    f"H-MEM routing: L{layer} searching {candidates.count()} "
                    f"children of parent hits"
                )
                return self._rank_by_similarity(
                    candidates,
                    query_embedding,
                    top_k,
                    similarity_threshold=similarity_threshold,
                )

            # Routing found no candidates, fall through to fallback
            logger.debug(f"H-MEM routing: L{layer} no children found, using fallback")

        # Fallback: prefix-based search (less efficient but ensures results)
        index_pattern = self._build_index_pattern(
            layer, fallback_project_id, fallback_chart_id, fallback_node_id
        )
        candidates = HMEMLayerEmbedding.objects.filter(
            layer=layer,
            positional_index__startswith=index_pattern,
        )

        return self._rank_by_similarity(
            candidates,
            query_embedding,
            top_k,
            similarity_threshold=similarity_threshold,
        )

    def _collect_child_indices(self, results: list[HMEMRetrievalResult]) -> list[str]:
        """
        Collect child indices from parent results for routing.

        This implements the union in H-MEM's formula:
        M_k^(l) = ⋃_{x∈M_k^(l-1)} TopK_{y∈Child(x)} (sim(q,y))
        """
        child_indices: list[str] = []
        for r in results:
            if r.child_indices:
                child_indices.extend(r.child_indices)
        return child_indices

    def _rank_by_similarity(
        self,
        candidates,
        query_embedding: list[float],
        top_k: int,
        similarity_threshold: Optional[float] = None,
    ) -> list[HMEMRetrievalResult]:
        """Rank candidates by cosine similarity and return top-k."""
        results: list[HMEMRetrievalResult] = []
        query_np = np.array(query_embedding)

        l2_allowed = {
            "chart_overview",
            "chart_nodes",
        }
        for candidate in candidates:
            if candidate.layer == 2:
                path_hash = getattr(candidate, "path_hash", "")
                if path_hash not in l2_allowed and not path_hash.startswith(
                    "chart_mechanic_"
                ):
                    continue
            candidate_embedding = np.array(candidate.embedding)
            similarity = self._cosine_similarity(query_np, candidate_embedding)

            results.append(
                HMEMRetrievalResult(
                    layer=candidate.layer,
                    layer_name=LAYER_NAMES.get(candidate.layer, f"L{candidate.layer}"),
                    content=candidate.content,
                    positional_index=candidate.positional_index,
                    similarity_score=float(similarity),
                    child_indices=candidate.child_indices or [],
                    metadata={
                        "id": candidate.id,
                        "node_id": str(candidate.node_id) if candidate.node else None,
                        "chart_id": (
                            str(candidate.chart_id) if candidate.chart else None
                        ),
                        "parent_index": candidate.parent_index,
                        "path_hash": getattr(candidate, "path_hash", ""),
                        "created_at": candidate.created_at.isoformat(),
                    },
                )
            )

        # Sort by similarity (descending) and take top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        if similarity_threshold is not None:
            return [r for r in results if r.similarity_score >= similarity_threshold]
        return results[:top_k]

    def _build_index_pattern(
        self,
        layer: int,
        project_id: str,
        chart_id: Optional[str],
        node_id: Optional[str],
    ) -> str:
        """Build positional index prefix pattern for fallback filtering."""
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
