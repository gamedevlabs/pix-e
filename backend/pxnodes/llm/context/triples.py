"""
Knowledge Triple extraction for PX Nodes and Charts.

Based on Zeng et al. (2024) "On the Structural Memory of LLM Agents".
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Union

from pxcharts.models import PxChart, PxChartContainer, PxChartEdge
from pxnodes.models import PxComponent, PxNode

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class KnowledgeTriple:
    """Represents a knowledge triple (head, relation, tail)."""

    head: str
    relation: str
    tail: Union[str, int, float, bool]

    def to_tuple(self) -> tuple[str, str, Any]:
        """Convert to tuple format."""
        return (self.head, self.relation, self.tail)

    def __str__(self) -> str:
        """String representation for context output."""
        if isinstance(self.tail, str):
            tail_str = f'"{self.tail}"'
        elif isinstance(self.tail, bool):
            tail_str = str(self.tail).lower()
        else:
            tail_str = str(self.tail)
        return f"({self.head}, {self.relation}, {tail_str})"


def extract_node_triples(node: PxNode) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxNode.

    Triples extracted:
    - Node identity: (node_id, is_type, PX_Node)
    - Node title: (node_id, has_title, name)
    - Component values: (node_id, has_component_{name}, value)
    """
    node_id = str(node.id)
    triples: list[KnowledgeTriple] = []

    # Node identity
    triples.append(KnowledgeTriple(node_id, "is_type", "PX_Node"))

    # Node title
    triples.append(KnowledgeTriple(node_id, "has_title", node.name))

    # Node has description (boolean indicator)
    if node.description and node.description.strip():
        triples.append(KnowledgeTriple(node_id, "has_description", True))

    return triples


def extract_component_triples(component: PxComponent) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxComponent.

    Triples extracted:
    - (node_id, has_component_{definition_name}, value)
    - (node_id, has_component_type_{definition_name}, type)
    """
    node_id = str(component.node.id)
    definition_name = component.definition.name.lower().replace(" ", "_")
    triples: list[KnowledgeTriple] = []

    # Component value
    triples.append(
        KnowledgeTriple(
            node_id,
            f"has_component_{definition_name}",
            component.value,
        )
    )

    # Component type
    triples.append(
        KnowledgeTriple(
            node_id,
            f"has_component_type_{definition_name}",
            component.definition.type,
        )
    )

    return triples


def extract_edge_triples(edge: PxChartEdge) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxChartEdge.

    Triples extracted:
    - (source_container_id, leads_to, target_container_id)
    - (source_node_id, leads_to_node, target_node_id) if both have content
    """
    triples: list[KnowledgeTriple] = []

    if edge.source and edge.target:
        source_id = str(edge.source.id)
        target_id = str(edge.target.id)

        # Container-level edge
        triples.append(KnowledgeTriple(source_id, "leads_to", target_id))

        # Node-level edge (if containers have node content)
        if edge.source.content and edge.target.content:
            source_node_id = str(edge.source.content.id)
            target_node_id = str(edge.target.content.id)
            triples.append(
                KnowledgeTriple(source_node_id, "leads_to_node", target_node_id)
            )

    return triples


def extract_container_triples(container: PxChartContainer) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxChartContainer.

    Triples extracted:
    - (container_id, is_type, PX_Container)
    - (container_id, has_name, name)
    - (container_id, contains_node, node_id) if has content
    - (container_id, belongs_to_chart, chart_id)
    """
    container_id = str(container.id)
    triples: list[KnowledgeTriple] = []

    # Container identity
    triples.append(KnowledgeTriple(container_id, "is_type", "PX_Container"))

    # Container name
    triples.append(KnowledgeTriple(container_id, "has_name", container.name))

    # Container content (linked node)
    if container.content:
        triples.append(
            KnowledgeTriple(container_id, "contains_node", str(container.content.id))
        )

    # Chart membership
    triples.append(
        KnowledgeTriple(container_id, "belongs_to_chart", str(container.px_chart.id))
    )

    return triples


def extract_all_triples(
    node: PxNode,
    chart: Optional[PxChart] = None,
    include_neighbors: bool = True,
) -> list[KnowledgeTriple]:
    """
    Extract all knowledge triples for a node and its context.

    Args:
        node: The target PxNode
        chart: Optional PxChart for edge relationships
        include_neighbors: Whether to include neighbor node triples

    Returns:
        List of KnowledgeTriple objects
    """
    all_triples: list[KnowledgeTriple] = []

    # Node triples
    all_triples.extend(extract_node_triples(node))

    # Component triples
    for component in node.components.all():
        all_triples.extend(extract_component_triples(component))

    # Chart-related triples
    if chart:
        # Find container(s) containing this node
        containers = chart.containers.filter(content=node)
        for container in containers:
            all_triples.extend(extract_container_triples(container))

            # Edge triples from this container
            for edge in container.outgoing_edges.all():
                all_triples.extend(extract_edge_triples(edge))

            for edge in container.incoming_edges.all():
                all_triples.extend(extract_edge_triples(edge))

    return all_triples


def compute_derived_triples(
    target_node: PxNode,
    previous_nodes: list[PxNode],
    next_nodes: list[PxNode],
) -> list[KnowledgeTriple]:
    """
    Compute derived triples from node relationships.

    Derived triples include:
    - Component value deltas between nodes
    - Component transitions between nodes
    """
    derived: list[KnowledgeTriple] = []
    target_id = str(target_node.id)

    target_components = _get_component_map(target_node)

    # Compute deltas from previous nodes
    for prev_node in previous_nodes:
        prev_components = _get_component_map(prev_node)

        for name, target_value in target_components.items():
            if name not in prev_components:
                continue
            prev_value = prev_components[name]
            if isinstance(target_value, (int, float)) and isinstance(
                prev_value, (int, float)
            ):
                delta = target_value - prev_value
                delta_str = f"+{delta}" if delta >= 0 else str(delta)
                derived.append(
                    KnowledgeTriple(
                        target_id,
                        f"component_delta_{name}_from_{prev_node.id}",
                        delta_str,
                    )
                )

                # Classify the transition
                if abs(delta) > 50:
                    transition_type = "spike" if delta > 0 else "drop"
                elif abs(delta) > 20:
                    transition_type = "rise" if delta > 0 else "fall"
                else:
                    transition_type = "stable"

                derived.append(
                    KnowledgeTriple(
                        target_id,
                        f"component_transition_{name}_from_{prev_node.id}",
                        transition_type,
                    )
                )
            elif target_value != prev_value:
                derived.append(
                    KnowledgeTriple(
                        target_id,
                        f"component_change_{name}_from_{prev_node.id}",
                        f"{prev_value} -> {target_value}",
                    )
                )

    return derived


def _get_component_value(
    node: PxNode, component_name: str
) -> Optional[Union[int, float, str, bool]]:
    """Get a component value from a node by definition name."""
    try:
        component = node.components.filter(
            definition__name__iexact=component_name
        ).first()
        if component:
            return component.value
    except Exception:
        pass
    return None


def _get_component_map(node: PxNode) -> dict[str, Any]:
    """Get a map of component definition names to values."""
    components: dict[str, Any] = {}
    for comp in node.components.select_related("definition").all():
        definition_name = comp.definition.name.lower().replace(" ", "_")
        components[definition_name] = comp.value
    return components


# =============================================================================
# LLM-Based Triple Extraction (from Zeng et al. 2024)
# =============================================================================


def parse_llm_triples(response: str) -> list[KnowledgeTriple]:
    """
    Parse knowledge triples from LLM response.

    Expected format from the paper:
    <head entity; relation; tail entity>
    """
    triples: list[KnowledgeTriple] = []

    # Match pattern: <head; relation; tail>
    pattern = r"<([^;]+);\s*([^;]+);\s*([^>]+)>"
    matches = re.findall(pattern, response)

    for head, relation, tail in matches:
        head = head.strip()
        relation = relation.strip()
        tail = tail.strip()

        if head and relation and tail:
            triples.append(KnowledgeTriple(head, relation, tail))

    return triples


def get_node_components_for_prompt(node: PxNode) -> list[dict[str, Any]]:
    """Get components from a node formatted for prompt inclusion."""
    components: list[dict[str, Any]] = []

    for comp in node.components.select_related("definition").all():
        components.append(
            {
                "definition_name": comp.definition.name,
                "definition_type": comp.definition.type,
                "value": comp.value,
            }
        )

    return components


def extract_narrative_triples(
    node: PxNode,
    llm_provider: LLMProvider,
) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from narrative text using LLM.

    This uses the paper's prompt to extract relationships from the
    node description that aren't captured by deterministic extraction.

    Args:
        node: The PxNode to extract triples from
        llm_provider: LLM provider for generation

    Returns:
        List of KnowledgeTriple objects extracted from narrative
    """
    from pxnodes.llm.context.prompts import (
        KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT,
        format_components_for_prompt,
    )

    # Get components
    components = get_node_components_for_prompt(node)
    components_text = format_components_for_prompt(components)

    # Use description or fallback
    description = node.description or "No description provided."

    # Build prompt
    prompt = KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT.format(
        title=node.name,
        description=description,
        components=components_text,
    )

    # Generate using LLM
    try:
        response = llm_provider.generate(prompt)
        triples = parse_llm_triples(response)
        return triples
    except Exception as e:
        logger.warning(f"Failed to extract narrative triples for node {node.id}: {e}")
        return []


def extract_all_triples_with_llm(
    node: PxNode,
    chart: Optional[PxChart] = None,
    llm_provider: Optional[LLMProvider] = None,
) -> list[KnowledgeTriple]:
    """
    Extract all triples: deterministic (structured) + LLM (narrative).

    Combines:
    1. Deterministic triples from components, edges, etc.
    2. LLM-extracted triples from description text

    Args:
        node: The target PxNode
        chart: Optional PxChart for edge relationships
        llm_provider: Optional LLM provider for narrative extraction

    Returns:
        Combined list of KnowledgeTriple objects
    """
    all_triples: list[KnowledgeTriple] = []

    # Deterministic triples (always extracted)
    all_triples.extend(extract_all_triples(node, chart, include_neighbors=False))

    # LLM-based narrative triples (if provider available)
    if llm_provider and node.description:
        narrative_triples = extract_narrative_triples(node, llm_provider)
        all_triples.extend(narrative_triples)

    return all_triples


def extract_llm_triples_only(
    node: PxNode,
    llm_provider: LLMProvider,
) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples using LLM only.

    This mirrors the paper's approach by relying on LLM extraction from
    narrative text (with components included in the prompt) instead of
    deterministic triples.
    """
    if not llm_provider:
        return []
    return extract_narrative_triples(node, llm_provider)
