"""
Change detection for Structural Memory generation.

Computes content hashes to detect when nodes need re-processing.
Considers: node name, description, components, and edges.
"""

import hashlib
import json
import logging
from typing import Optional

from pxcharts.models import PxChart
from pxnodes.models import PxNode, StructuralMemoryState

logger = logging.getLogger(__name__)


def compute_node_content_hash(node: PxNode, chart: PxChart) -> str:
    """
    Compute a content hash for a node in the context of a chart.

    Includes:
    - Node name and description
    - All component values (sorted by definition name)
    - All edges involving this node's container (sorted)

    Args:
        node: The PxNode to hash
        chart: The chart context (for edge information)

    Returns:
        SHA-256 hash string (64 chars)
    """
    # Build content dictionary
    content = {
        "node_id": str(node.id),
        "name": node.name,
        "description": node.description or "",
        "components": [],
        "edges": [],
    }

    # Add components (sorted by definition name for consistency)
    components = node.components.select_related("definition").order_by("definition__name")
    for comp in components:
        content["components"].append(
            {
                "definition": comp.definition.name,
                "type": comp.definition.type,
                "value": comp.value,
            }
        )

    # Find container(s) for this node in the chart
    containers = chart.containers.filter(content=node)

    # Add edges (sorted for consistency)
    edge_data = []
    for container in containers:
        # Outgoing edges
        for edge in container.outgoing_edges.all():
            if edge.target:
                edge_data.append(
                    {
                        "direction": "outgoing",
                        "source": str(container.id),
                        "target": str(edge.target.id),
                        "target_node": str(edge.target.content.id)
                        if edge.target.content
                        else None,
                    }
                )

        # Incoming edges
        for edge in container.incoming_edges.all():
            if edge.source:
                edge_data.append(
                    {
                        "direction": "incoming",
                        "source": str(edge.source.id),
                        "target": str(container.id),
                        "source_node": str(edge.source.content.id)
                        if edge.source.content
                        else None,
                    }
                )

    # Sort edges by source+target for consistency
    edge_data.sort(key=lambda e: (e.get("source", ""), e.get("target", "")))
    content["edges"] = edge_data

    # Serialize and hash
    content_json = json.dumps(content, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content_json.encode()).hexdigest()


def has_node_changed(node: PxNode, chart: PxChart) -> bool:
    """
    Check if a node has changed since last processing.

    Args:
        node: The node to check
        chart: The chart context

    Returns:
        True if node needs re-processing, False if unchanged
    """
    current_hash = compute_node_content_hash(node, chart)

    try:
        state = StructuralMemoryState.objects.get(node=node, chart=chart)
        return state.content_hash != current_hash
    except StructuralMemoryState.DoesNotExist:
        # Never processed before
        return True


def get_changed_nodes(chart: PxChart) -> tuple[list[PxNode], list[PxNode]]:
    """
    Get lists of changed and unchanged nodes for a chart.

    Args:
        chart: The chart to check

    Returns:
        Tuple of (changed_nodes, unchanged_nodes)
    """
    changed = []
    unchanged = []

    # Get all nodes in the chart
    containers = chart.containers.filter(content__isnull=False).select_related("content")
    nodes = [c.content for c in containers]

    for node in nodes:
        if has_node_changed(node, chart):
            changed.append(node)
        else:
            unchanged.append(node)

    return changed, unchanged


def update_processing_state(
    node: PxNode,
    chart: PxChart,
    triples_count: int = 0,
    facts_count: int = 0,
    embeddings_count: int = 0,
) -> StructuralMemoryState:
    """
    Update or create processing state after successful generation.

    Args:
        node: The processed node
        chart: The chart context
        triples_count: Number of triples generated
        facts_count: Number of facts extracted
        embeddings_count: Number of embeddings stored

    Returns:
        The updated StructuralMemoryState
    """
    content_hash = compute_node_content_hash(node, chart)

    state, _ = StructuralMemoryState.objects.update_or_create(
        node=node,
        chart=chart,
        defaults={
            "content_hash": content_hash,
            "triples_count": triples_count,
            "facts_count": facts_count,
            "embeddings_count": embeddings_count,
        },
    )

    return state


def get_processing_stats(chart: PxChart) -> dict:
    """
    Get processing statistics for a chart.

    Returns dict with:
    - total_nodes: Total nodes in chart
    - processed_nodes: Nodes with existing structural memory
    - pending_nodes: Nodes that need processing
    - total_triples: Sum of triples across all processed nodes
    - total_facts: Sum of facts across all processed nodes
    - total_embeddings: Sum of embeddings across all processed nodes
    """
    containers = chart.containers.filter(content__isnull=False)
    total_nodes = containers.count()

    states = StructuralMemoryState.objects.filter(chart=chart)
    processed_count = states.count()

    # Check how many are actually up-to-date
    changed, unchanged = get_changed_nodes(chart)

    aggregates = states.aggregate(
        total_triples=models.Sum("triples_count"),
        total_facts=models.Sum("facts_count"),
        total_embeddings=models.Sum("embeddings_count"),
    )

    return {
        "total_nodes": total_nodes,
        "processed_nodes": len(unchanged),
        "pending_nodes": len(changed),
        "total_triples": aggregates["total_triples"] or 0,
        "total_facts": aggregates["total_facts"] or 0,
        "total_embeddings": aggregates["total_embeddings"] or 0,
    }


# Need to import models at module level for aggregate
from django.db import models as models  # noqa: E402
