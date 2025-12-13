"""
Structural Memory Context Strategy - Main Entry Point.

Implements the Mixed Structural Memory approach from Zeng et al. (2024)
for converting PX Nodes/Charts into Knowledge Triples and Atomic Facts.

This module provides the high-level API for building structural context
that can be used with LLM evaluation handlers.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from pxcharts.models import PxChart
from pxnodes.llm.context.facts import AtomicFact, extract_atomic_facts
from pxnodes.llm.context.graph_retrieval import GraphSlice, get_graph_slice
from pxnodes.llm.context.serializer import (
    build_minimal_context,
    build_structural_context,
    context_to_dict,
)
from pxnodes.llm.context.triples import (
    KnowledgeTriple,
    compute_derived_triples,
    extract_all_triples,
)
from pxnodes.models import PxNode


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class StructuralMemoryResult:
    """Result of structural memory context building."""

    context: str
    graph_slice: GraphSlice
    triples: list[KnowledgeTriple] = field(default_factory=list)
    facts: list[AtomicFact] = field(default_factory=list)
    derived_triples: list[KnowledgeTriple] = field(default_factory=list)

    @property
    def triple_count(self) -> int:
        """Total number of triples extracted."""
        return len(self.triples) + len(self.derived_triples)

    @property
    def fact_count(self) -> int:
        """Total number of atomic facts extracted."""
        return len(self.facts)

    @property
    def neighbor_count(self) -> int:
        """Number of neighbor nodes in context."""
        return len(self.graph_slice.previous_nodes) + len(self.graph_slice.next_nodes)


class StructuralMemoryContext:
    """
    Main class for building Structural Memory context.

    Usage:
        context_builder = StructuralMemoryContext(llm_provider)
        result = context_builder.build(target_node, chart)
        prompt = f"Evaluate coherence:\\n{result.context}"
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        skip_fact_extraction: bool = False,
    ):
        """
        Initialize the context builder.

        Args:
            llm_provider: LLM provider for atomic fact extraction
            skip_fact_extraction: If True, skip LLM-based fact extraction
        """
        self.llm_provider = llm_provider
        self.skip_fact_extraction = skip_fact_extraction

    def build(
        self,
        target_node: PxNode,
        chart: PxChart,
        depth: int = 1,
    ) -> StructuralMemoryResult:
        """
        Build structural memory context for a target node.

        Args:
            target_node: The node to build context for
            chart: The chart containing the node
            depth: How many levels of neighbors to include

        Returns:
            StructuralMemoryResult with context and metadata
        """
        # Get graph slice
        graph_slice = get_graph_slice(target_node, chart, depth=depth)

        # Extract triples
        all_triples: list[KnowledgeTriple] = []
        all_triples.extend(
            extract_all_triples(target_node, chart, include_neighbors=False)
        )
        for node in graph_slice.previous_nodes + graph_slice.next_nodes:
            all_triples.extend(
                extract_all_triples(node, chart, include_neighbors=False)
            )

        # Extract atomic facts (if provider available)
        all_facts: list[AtomicFact] = []
        if self.llm_provider and not self.skip_fact_extraction:
            all_facts.extend(extract_atomic_facts(target_node, self.llm_provider))
            for node in graph_slice.previous_nodes:
                all_facts.extend(extract_atomic_facts(node, self.llm_provider))

        # Compute derived triples
        derived_triples = compute_derived_triples(
            target_node,
            graph_slice.previous_nodes,
            graph_slice.next_nodes,
        )

        # Build context string
        context = build_structural_context(
            target_node,
            chart,
            self.llm_provider,
            skip_fact_extraction=self.skip_fact_extraction,
        )

        return StructuralMemoryResult(
            context=context,
            graph_slice=graph_slice,
            triples=all_triples,
            facts=all_facts,
            derived_triples=derived_triples,
        )

    def build_minimal(
        self,
        target_node: PxNode,
        chart: Optional[PxChart] = None,
    ) -> str:
        """
        Build minimal context with just triples (no LLM extraction).

        Useful for quick operations or when LLM is not available.
        """
        return build_minimal_context(target_node, chart)

    def build_as_dict(
        self,
        target_node: PxNode,
        chart: PxChart,
    ) -> dict[str, Any]:
        """
        Build context as dictionary for debugging/logging.

        Returns structured data instead of formatted string.
        """
        return context_to_dict(target_node, chart, self.llm_provider)


# Convenience function for one-off context building
def build_context(
    target_node: PxNode,
    chart: PxChart,
    llm_provider: Optional[LLMProvider] = None,
    depth: int = 1,
) -> str:
    """
    Convenience function to build structural context.

    Args:
        target_node: The node to build context for
        chart: The chart containing the node
        llm_provider: Optional LLM provider for fact extraction
        depth: How many levels of neighbors to include

    Returns:
        Formatted context string
    """
    builder = StructuralMemoryContext(llm_provider=llm_provider)
    result = builder.build(target_node, chart, depth=depth)
    return result.context


def get_context_stats(
    target_node: PxNode,
    chart: PxChart,
    llm_provider: Optional[LLMProvider] = None,
) -> dict[str, int]:
    """
    Get statistics about the context that would be built.

    Useful for thesis metrics and comparison.
    """
    builder = StructuralMemoryContext(llm_provider=llm_provider)
    result = builder.build(target_node, chart)

    return {
        "total_triples": result.triple_count,
        "base_triples": len(result.triples),
        "derived_triples": len(result.derived_triples),
        "atomic_facts": result.fact_count,
        "previous_nodes": len(result.graph_slice.previous_nodes),
        "next_nodes": len(result.graph_slice.next_nodes),
        "context_length": len(result.context),
    }
