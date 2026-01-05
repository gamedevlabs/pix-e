"""
Graph traversal utilities for Hierarchical Graph strategy.

Implements BFS/DFS traversal for trace reconstruction:
- Reverse traversal from target to start/checkpoint
- Forward traversal for lookahead context

Note: The HierarchicalGraphStrategy now uses get_backward_paths_to_node and
get_forward_paths_from_node from shared/graph_retrieval.py for explicit
path enumeration. The BFS functions here are kept for backwards compatibility.
"""

from collections import deque
from typing import Any, Optional


def reverse_bfs(
    target_node: Any,
    chart: Any,
    max_depth: Optional[int] = None,
    stop_at_checkpoint: bool = True,
) -> list[Any]:
    """
    Perform reverse BFS from target node to reconstruct the path.

    Walks backward through the graph following incoming edges
    until reaching the start or a checkpoint.

    Args:
        target_node: The node to start traversal from
        chart: The chart containing the nodes
        max_depth: Maximum number of nodes to traverse (None = unlimited)
        stop_at_checkpoint: Stop at checkpoint nodes if found

    Returns:
        List of nodes in path order (start to target, excluding target)
    """
    path: list[Any] = []
    visited: set[str] = set()
    queue: deque[tuple[Any, int]] = deque()

    # Find container for target node
    target_container = _find_container_for_node(target_node, chart)
    if not target_container:
        return []

    # Start with target's predecessors
    incoming_edges = getattr(target_container, "incoming_edges", None)
    if incoming_edges:
        edge_list = incoming_edges.all() if hasattr(incoming_edges, "all") else []
        for edge in edge_list:
            source = getattr(edge, "source", None)
            if source:
                queue.append((source, 1))

    # BFS backward
    while queue:
        container, depth = queue.popleft()

        if max_depth and depth > max_depth:
            continue

        container_id = str(getattr(container, "id", ""))
        if container_id in visited:
            continue
        visited.add(container_id)

        # Get the node content from container
        node = getattr(container, "content", None)
        if node:
            path.append(node)

            # Check for checkpoint
            if stop_at_checkpoint and _is_checkpoint(node):
                break

        # Add predecessors to queue
        incoming = getattr(container, "incoming_edges", None)
        if incoming:
            edges = incoming.all() if hasattr(incoming, "all") else []
            for edge in edges:
                source = getattr(edge, "source", None)
                if source:
                    source_id = str(getattr(source, "id", ""))
                    if source_id not in visited:
                        queue.append((source, depth + 1))

    # Reverse to get start-to-target order
    path.reverse()
    return path


def forward_bfs(
    target_node: Any,
    chart: Any,
    max_depth: Optional[int] = 1,
) -> list[Any]:
    """
    Perform forward BFS from target node for lookahead context.

    Args:
        target_node: The node to start from
        chart: The chart containing the nodes
        max_depth: Maximum depth to traverse (default 1 = immediate successors,
                   None = unlimited)

    Returns:
        List of successor nodes
    """
    successors: list[Any] = []
    visited: set[str] = set()
    queue: deque[tuple[Any, int]] = deque()

    # Find container for target node
    target_container = _find_container_for_node(target_node, chart)
    if not target_container:
        return []

    # Start with target's successors
    outgoing_edges = getattr(target_container, "outgoing_edges", None)
    if outgoing_edges:
        edge_list = outgoing_edges.all() if hasattr(outgoing_edges, "all") else []
        for edge in edge_list:
            target_edge = getattr(edge, "target", None)
            if target_edge:
                queue.append((target_edge, 1))

    # BFS forward
    while queue:
        container, depth = queue.popleft()

        if max_depth is not None and depth > max_depth:
            continue

        container_id = str(getattr(container, "id", ""))
        if container_id in visited:
            continue
        visited.add(container_id)

        # Get the node content from container
        node = getattr(container, "content", None)
        if node:
            successors.append(node)

        # Add successors to queue if not at max depth
        if max_depth is None or depth < max_depth:
            outgoing = getattr(container, "outgoing_edges", None)
            if outgoing:
                edges = outgoing.all() if hasattr(outgoing, "all") else []
                for edge in edges:
                    target_edge = getattr(edge, "target", None)
                    if target_edge:
                        target_id = str(getattr(target_edge, "id", ""))
                        if target_id not in visited:
                            queue.append((target_edge, depth + 1))

    return successors


def _find_container_for_node(node: Any, chart: Any) -> Optional[Any]:
    """Find the chart container that contains a given node."""
    containers = getattr(chart, "containers", None)
    if not containers:
        return None

    container_qs = (
        containers.filter(content_id=getattr(node, "id", None))
        if hasattr(containers, "filter")
        else []
    )
    if container_qs:
        return container_qs.first() if hasattr(container_qs, "first") else None

    chart_edges = getattr(chart, "edges", None)
    if chart_edges and hasattr(chart_edges, "filter"):
        edge = (
            chart_edges.filter(source__content_id=getattr(node, "id", None))
            .select_related("source")
            .first()
        )
        if edge and getattr(edge, "source", None):
            return edge.source
        edge = (
            chart_edges.filter(target__content_id=getattr(node, "id", None))
            .select_related("target")
            .first()
        )
        if edge and getattr(edge, "target", None):
            return edge.target

    # Fallback: iterate through containers
    container_list = (
        containers.all() if hasattr(containers, "all") else list(containers)
    )
    for container in container_list:
        if getattr(container, "content", None) == node:
            return container

    return None


def _is_checkpoint(node: Any) -> bool:
    """Check if a node is a checkpoint/save point."""
    # Check components
    components = getattr(node, "components", None)
    if components:
        comp_list = components.all() if hasattr(components, "all") else []
        for comp in comp_list:
            definition = getattr(comp, "definition", None)
            if definition:
                def_name = getattr(definition, "name", "").lower()
                if "checkpoint" in def_name or "save" in def_name:
                    return True

    # Check name
    node_name = getattr(node, "name", "").lower()
    if "checkpoint" in node_name or "save point" in node_name:
        return True

    return False
