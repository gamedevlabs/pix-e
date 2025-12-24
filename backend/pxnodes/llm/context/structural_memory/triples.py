"""
Knowledge Triple extraction for PX Nodes and Charts.

Based on Zeng et al. (2024) "On the Structural Memory of LLM Agents".

Triples are stored in the vector store (memory_embeddings table) by the
StructuralMemoryGenerator. This module supports LLM-based triple extraction
following Zeng et al. (2024).
"""

import asyncio
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


def get_cached_triples_from_vector_store(
    node_id: str, chart_id: Optional[str] = None
) -> list[KnowledgeTriple]:
    """
    Retrieve cached knowledge triples from the vector store.

    Returns empty list if no cached triples found.
    """
    try:
        from pxnodes.llm.context.vector_store import VectorStore

        vector_store = VectorStore()
        memories = vector_store.get_memories_by_node(
            node_id=node_id,
            memory_type="knowledge_triple",
            chart_id=chart_id,
        )
        vector_store.close()

        if memories:
            logger.debug(f"Found {len(memories)} cached triples for node {node_id}")
            triples = []
            for m in memories:
                metadata = m.get("metadata", {})
                head = metadata.get("head", "")
                relation = metadata.get("relation", "")
                tail = metadata.get("tail", "")
                if head and relation:
                    triples.append(KnowledgeTriple(head, relation, tail))
            return triples
    except Exception as e:
        logger.warning(f"Failed to retrieve cached triples from vector store: {e}")

    return []


def extract_node_triples(node: PxNode) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxNode.

    Triples extracted:
    - Node identity: (node_name, is_type, PX_Node)
    - Component values: (node_name, has_{component_name}, value)

    Uses node.name as head for human readability and LLM comprehension.
    """
    node_name = node.name
    triples: list[KnowledgeTriple] = []

    # Node identity
    triples.append(KnowledgeTriple(node_name, "is_type", "PX_Node"))

    # Node has description (boolean indicator)
    if node.description and node.description.strip():
        triples.append(KnowledgeTriple(node_name, "has_description", True))

    return triples


def extract_component_triples(component: PxComponent) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxComponent.

    Triples extracted:
    - (node_name, has_{definition_name}, value)

    Uses node.name as head for human readability and LLM comprehension.
    """
    node_name = component.node.name
    definition_name = component.definition.name.lower().replace(" ", "_")
    triples: list[KnowledgeTriple] = []

    # Component value - use cleaner relation name
    triples.append(
        KnowledgeTriple(
            node_name,
            f"has_{definition_name}",
            component.value,
        )
    )

    return triples


def extract_edge_triples(edge: PxChartEdge) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxChartEdge.

    Triples extracted:
    - (source_node_name, leads_to, target_node_name) if both have content

    Uses node names for human readability and LLM comprehension.
    """
    triples: list[KnowledgeTriple] = []

    if edge.source and edge.target:
        # Node-level edge (if containers have node content)
        if edge.source.content and edge.target.content:
            source_name = edge.source.content.name
            target_name = edge.target.content.name
            triples.append(KnowledgeTriple(source_name, "leads_to", target_name))

    return triples


def extract_container_triples(container: PxChartContainer) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples from a PxChartContainer.

    Triples extracted:
    - (node_name, in_chart, chart_name) if container has node content

    Uses node/chart names for human readability and LLM comprehension.
    """
    triples: list[KnowledgeTriple] = []

    # Only create triples if container has node content
    if container.content:
        node_name = container.content.name
        chart_name = container.px_chart.name

        # Node's chart membership
        triples.append(KnowledgeTriple(node_name, "in_chart", chart_name))

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

    Uses node names for human readability and LLM comprehension.
    """
    derived: list[KnowledgeTriple] = []
    target_name = target_node.name

    target_components = _get_component_map(target_node)

    # Compute deltas from previous nodes
    for prev_node in previous_nodes:
        prev_name = prev_node.name
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
                        target_name,
                        f"component_delta_{name}_from_{prev_name}",
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
                        target_name,
                        f"component_transition_{name}_from_{prev_name}",
                        transition_type,
                    )
                )
            elif target_value != prev_value:
                derived.append(
                    KnowledgeTriple(
                        target_name,
                        f"component_change_{name}_from_{prev_name}",
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
    from pxnodes.llm.context.shared.prompts import (
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
        response = llm_provider.generate(prompt, operation="node_triples")
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


async def extract_all_triples_async(
    node: PxNode,
    chart: Optional[PxChart],
    llm_provider: Optional[LLMProvider] = None,
) -> list[KnowledgeTriple]:
    """
    Async version of extract_all_triples_with_llm for parallel execution.

    Extracts deterministic triples and optionally LLM-based narrative triples.
    Uses thread_sensitive=False for LLM calls to enable true parallelism.
    """
    import logfire
    from asgiref.sync import sync_to_async

    from pxnodes.llm.context.shared.prompts import (
        KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT,
        format_components_for_prompt,
    )

    node_id = str(node.id)
    node_name = node.name

    with logfire.span(
        "extract_knowledge_triples",
        node_id=node_id,
        node_name=node_name,
    ):
        all_triples: list[KnowledgeTriple] = []

        # Deterministic triples (sync Django ORM calls - must use thread_sensitive=True)
        logfire.info("extracting_deterministic_triples", node_name=node_name)
        deterministic_triples = await sync_to_async(
            extract_all_triples, thread_sensitive=True
        )(node, chart, include_neighbors=False)
        all_triples.extend(deterministic_triples)

        # LLM-based narrative triples (if provider available and node has description)
        if llm_provider and node.description:
            logfire.info("extracting_narrative_triples", node_name=node_name)
            try:
                # First: fetch components (Django ORM - thread_sensitive=True)
                components = await sync_to_async(
                    get_node_components_for_prompt, thread_sensitive=True
                )(node)
                components_text = format_components_for_prompt(components)

                # Build prompt
                description = node.description or "No description provided."
                prompt = KNOWLEDGE_TRIPLE_EXTRACTION_PROMPT.format(
                    title=node_name,
                    description=description,
                    components=components_text,
                )

                # Then: LLM call (HTTP - thread_sensitive=False for parallelism)
                response = await sync_to_async(
                    llm_provider.generate, thread_sensitive=False
                )(prompt, operation="node_triples")
                narrative_triples = parse_llm_triples(response)
                all_triples.extend(narrative_triples)

                logfire.info(
                    "narrative_triples_extracted",
                    node_name=node_name,
                    count=len(narrative_triples),
                )
            except Exception as e:
                logger.warning(
                    f"Failed to extract narrative triples for {node_name}: {e}"
                )
                logfire.error(
                    "narrative_triples_failed",
                    node_name=node_name,
                    error=str(e),
                )

        logfire.info(
            "knowledge_triples_extracted",
            node_name=node_name,
            total_count=len(all_triples),
        )
        return all_triples


def extract_llm_triples_only(
    node: PxNode,
    llm_provider: LLMProvider,
) -> list[KnowledgeTriple]:
    """
    Extract knowledge triples using LLM only.

    This follows the paper's approach by relying on LLM extraction from
    narrative text (with components included in the prompt) instead of
    deterministic triples.
    """
    if not llm_provider:
        return []
    return extract_narrative_triples(node, llm_provider)


def extract_llm_triples_only_cached(
    node: PxNode,
    llm_provider: Optional[LLMProvider],
    chart_id: Optional[str] = None,
    force_regenerate: bool = False,
) -> list[KnowledgeTriple]:
    """Extract triples with optional vector store cache reuse."""
    if not force_regenerate:
        cached = get_cached_triples_from_vector_store(str(node.id), chart_id=chart_id)
        if cached:
            return cached
    if not llm_provider:
        return []
    return extract_narrative_triples(node, llm_provider)


async def extract_llm_triples_only_async(
    node: PxNode,
    llm_provider: LLMProvider,
) -> list[KnowledgeTriple]:
    """
    Async wrapper for LLM-only triple extraction.
    """
    if not llm_provider:
        return []
    return await asyncio.to_thread(extract_narrative_triples, node, llm_provider)
