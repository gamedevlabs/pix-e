"""
Context serializer for Mixed Structural Memory output.

Combines Knowledge Triples and Atomic Facts into the paper's format
for feeding to evaluation LLMs.
"""

from typing import Any, Optional

from pxcharts.models import PxChart
from pxnodes.llm.context.facts import AtomicFact, LLMProvider, extract_atomic_facts
from pxnodes.llm.context.graph_retrieval import GraphSlice, get_graph_slice
from pxnodes.llm.context.prompts import MIXED_CONTEXT_TEMPLATE
from pxnodes.llm.context.triples import (
    KnowledgeTriple,
    extract_all_triples,
    extract_llm_triples_only,
)
from pxnodes.models import PxNode


def format_triples_section(triples: list[KnowledgeTriple]) -> str:
    """Format a list of triples as context section."""
    if not triples:
        return "- No structural data available"

    lines = []
    for triple in triples:
        lines.append(f"- Triple: {triple}")
    return "\n".join(lines)


def format_facts_section(facts: list[AtomicFact]) -> str:
    """Format a list of facts as context section."""
    if not facts:
        return "- No narrative facts extracted"

    lines = []
    for i, fact in enumerate(facts, 1):
        lines.append(f"- Fact {i}: {fact.fact}")
    return "\n".join(lines)


def format_logic_checks(graph_slice: GraphSlice) -> str:
    """Format logic check section with basic context counts."""
    lines = [
        f"- Previous Nodes: {len(graph_slice.previous_nodes)}",
        f"- Next Nodes: {len(graph_slice.next_nodes)}",
    ]
    return "\n".join(lines)


def build_node_context_section(
    node: PxNode,
    chart: Optional[PxChart],
    facts: list[AtomicFact],
    llm_provider: Optional[LLMProvider],
    include_components: bool = True,
) -> str:
    """Build context section for a single node."""
    lines = []

    # Extract triples (LLM-only)
    triples: list[KnowledgeTriple] = []
    if llm_provider:
        triples = extract_llm_triples_only(node, llm_provider)

    # Add triples
    for triple in triples:
        lines.append(f"- Triple: {triple}")

    # Add facts
    node_facts = [f for f in facts if f.node_id == str(node.id)]
    for i, fact in enumerate(node_facts, 1):
        lines.append(f"- Fact: {fact.fact}")

    if not lines:
        lines.append(f"- Node: {node.name}")

    return "\n".join(lines)


def build_structural_context(
    target_node: PxNode,
    chart: PxChart,
    llm_provider: Optional[LLMProvider] = None,
    skip_fact_extraction: bool = False,
) -> str:
    """
    Build the complete mixed structural memory context.

    This is the main entry point for context generation.

    Args:
        target_node: The node being evaluated
        chart: The chart containing the node
        llm_provider: LLM provider for atomic fact extraction (optional)
        skip_fact_extraction: If True, skip LLM-based fact extraction

    Returns:
        Formatted mixed structural context string
    """
    # 1. Get graph slice (target + neighbors)
    graph_slice = get_graph_slice(target_node, chart, depth=1)

    # 2. Extract triples for all nodes (LLM-only)
    target_triples: list[KnowledgeTriple] = []
    if llm_provider:
        target_triples = extract_llm_triples_only(target_node, llm_provider)

    previous_triples: list[KnowledgeTriple] = []
    for node in graph_slice.previous_nodes:
        if llm_provider:
            previous_triples.extend(extract_llm_triples_only(node, llm_provider))

    next_triples: list[KnowledgeTriple] = []
    for node in graph_slice.next_nodes:
        if llm_provider:
            next_triples.extend(extract_llm_triples_only(node, llm_provider))

    # 3. Extract atomic facts (lazy, LLM-based)
    all_facts: list[AtomicFact] = []
    if llm_provider and not skip_fact_extraction:
        # Extract facts for target and previous nodes
        all_facts.extend(extract_atomic_facts(target_node, llm_provider))
        for node in graph_slice.previous_nodes:
            all_facts.extend(extract_atomic_facts(node, llm_provider))

    # 4. Format sections
    previous_context = format_triples_section(previous_triples)
    if graph_slice.previous_nodes:
        prev_facts = [
            f
            for f in all_facts
            if f.node_id in [str(n.id) for n in graph_slice.previous_nodes]
        ]
        if prev_facts:
            previous_context += "\n" + format_facts_section(prev_facts)

    target_context = format_triples_section(target_triples)
    target_facts = [f for f in all_facts if f.node_id == str(target_node.id)]
    if target_facts:
        target_context += "\n" + format_facts_section(target_facts)

    next_context = format_triples_section(next_triples)

    logic_checks = format_logic_checks(graph_slice)

    # 6. Assemble final context
    context = MIXED_CONTEXT_TEMPLATE.format(
        target_node_name=target_node.name,
        previous_context=previous_context,
        target_context=target_context,
        next_context=next_context,
        logic_checks=logic_checks,
    )

    return context


def build_minimal_context(
    target_node: PxNode,
    chart: Optional[PxChart] = None,
) -> str:
    """
    Build a minimal context with just triples (no LLM extraction).

    Useful for quick operations or when LLM is not available.
    """
    lines = ["[TARGET NODE TRIPLES]"]

    triples = extract_all_triples(target_node, chart, include_neighbors=False)
    for triple in triples:
        lines.append(f"- {triple}")

    if chart:
        graph_slice = get_graph_slice(target_node, chart, depth=1)

        if graph_slice.previous_nodes:
            lines.append("\n[PREVIOUS NODE TRIPLES]")
            for node in graph_slice.previous_nodes:
                node_triples = extract_all_triples(node, chart, include_neighbors=False)
                for triple in node_triples:
                    lines.append(f"- {triple}")

        if graph_slice.next_nodes:
            lines.append("\n[NEXT NODE TRIPLES]")
            for node in graph_slice.next_nodes:
                node_triples = extract_all_triples(node, chart, include_neighbors=False)
                for triple in node_triples:
                    lines.append(f"- {triple}")

    return "\n".join(lines)


def context_to_dict(
    target_node: PxNode,
    chart: PxChart,
    llm_provider: Optional[LLMProvider] = None,
) -> dict[str, Any]:
    """
    Build context as a dictionary (for debugging/logging).

    Returns structured data instead of formatted string.
    """
    graph_slice = get_graph_slice(target_node, chart, depth=1)

    target_triples: list[KnowledgeTriple] = []
    if llm_provider:
        target_triples = extract_llm_triples_only(target_node, llm_provider)

    all_facts: list[AtomicFact] = []
    if llm_provider:
        all_facts = extract_atomic_facts(target_node, llm_provider)

    return {
        "target": {
            "id": str(target_node.id),
            "name": target_node.name,
            "triples": [t.to_tuple() for t in target_triples],
            "facts": [f.fact for f in all_facts],
        },
        "previous_nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "triples": [
                    t.to_tuple()
                    for t in (
                        extract_llm_triples_only(n, llm_provider)
                        if llm_provider
                        else []
                    )
                ],
            }
            for n in graph_slice.previous_nodes
        ],
        "next_nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "triples": [
                    t.to_tuple()
                    for t in (
                        extract_llm_triples_only(n, llm_provider)
                        if llm_provider
                        else []
                    )
                ],
            }
            for n in graph_slice.next_nodes
        ],
        "derived_triples": [],
    }
