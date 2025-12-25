"""
Core types for context engineering strategies.

Defines the common data structures used across all strategies
for building and representing evaluation context.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from game_concept.models import GameConcept, Project
    from pillars.models import Pillar
    from pxcharts.models import PxChart
    from pxnodes.models import PxNode


class StrategyType(Enum):
    """Available context engineering strategies."""

    FULL_CONTEXT = "full_context"
    STRUCTURAL_MEMORY = "structural_memory"
    SIMPLE_SM = "simple_sm"
    HIERARCHICAL_GRAPH = "hierarchical_graph"
    HMEM = "hmem"
    COMBINED = "combined"


@dataclass
class LayerContext:
    """
    Context at a specific hierarchy layer (L1-L4).

    Used by hierarchical strategies to organize context
    at different levels of abstraction.
    """

    layer: int  # 1-4
    layer_name: str  # "domain", "category", "trace", "episode"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[list[float]] = None  # For H-MEM
    positional_index: Optional[str] = None  # For H-MEM routing

    def __str__(self) -> str:
        return f"[L{self.layer} {self.layer_name.upper()}]\n{self.content}"


@dataclass
class ContextResult:
    """
    Unified result from any context strategy.

    Contains the formatted context string for LLM prompts,
    plus structured data about what was included.

    Following Zeng et al. (2024), mixed memory includes:
    - Chunks: Raw text segments
    - Knowledge Triples: Structured relationships
    - Atomic Facts: Indivisible information units
    - Summaries: Condensed overviews
    """

    strategy: StrategyType
    context_string: str  # Formatted context for LLM prompt

    # Hierarchical context (for strategies 2-4)
    layers: list[LayerContext] = field(default_factory=list)

    # Mixed structural memory data (Zeng et al. 2024)
    chunks: list[Any] = field(default_factory=list)  # Chunk
    triples: list[Any] = field(default_factory=list)  # KnowledgeTriple
    facts: list[Any] = field(default_factory=list)  # AtomicFact
    summaries: list[Any] = field(default_factory=list)  # Summary

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def token_estimate(self) -> int:
        """Rough estimate of tokens in context (4 chars per token)."""
        return len(self.context_string) // 4

    @property
    def has_layers(self) -> bool:
        """Whether this result includes hierarchical layers."""
        return len(self.layers) > 0

    @property
    def has_triples(self) -> bool:
        """Whether this result includes knowledge triples."""
        return len(self.triples) > 0

    def get_layer(self, layer_num: int) -> Optional[LayerContext]:
        """Get a specific layer by number (1-4)."""
        for layer in self.layers:
            if layer.layer == layer_num:
                return layer
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "strategy": self.strategy.value,
            "context_string": self.context_string,
            "token_estimate": self.token_estimate,
            "layers": [
                {
                    "layer": layer_ctx.layer,
                    "name": layer_ctx.layer_name,
                    "content": layer_ctx.content,
                    "metadata": layer_ctx.metadata,
                }
                for layer_ctx in self.layers
            ],
            "chunks_count": len(self.chunks),
            "triples_count": len(self.triples),
            "facts_count": len(self.facts),
            "summaries_count": len(self.summaries),
            "metadata": self.metadata,
        }


@dataclass
class EvaluationScope:
    """
    Defines the scope of what to evaluate.

    Contains the target node, its chart context, and optionally
    project-level context (pillars, game concept).
    """

    target_node: "PxNode"
    chart: "PxChart"

    # Project-level context (for L1 layer)
    project: Optional["Project"] = None
    project_pillars: Optional[list["Pillar"]] = None
    game_concept: Optional["GameConcept"] = None

    # Evaluation options
    depth: int = 1  # How many neighbors to include
    include_paths: bool = True  # Whether to trace paths (L3)

    @property
    def has_project_context(self) -> bool:
        """Whether project-level context is available."""
        return bool(self.project_pillars or self.game_concept)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "target_node_id": str(self.target_node.id),
            "target_node_name": self.target_node.name,
            "chart_id": str(self.chart.id),
            "chart_name": self.chart.name,
            "pillars_count": len(self.project_pillars) if self.project_pillars else 0,
            "has_game_concept": self.game_concept is not None,
            "depth": self.depth,
            "include_paths": self.include_paths,
        }


# Layer name constants for consistency
LAYER_NAMES = {
    1: "domain",
    2: "category",
    3: "trace",
    4: "episode",
}


def get_layer_name(layer: int) -> str:
    """Get the name for a layer number."""
    return LAYER_NAMES.get(layer, f"layer_{layer}")
