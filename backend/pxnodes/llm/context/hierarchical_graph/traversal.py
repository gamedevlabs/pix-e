"""
Graph traversal utilities for Hierarchical Graph strategy.

Implements BFS/DFS traversal for trace reconstruction:
- Reverse traversal from target to start/checkpoint
- Forward traversal for lookahead context
- State aggregation along paths
"""

from collections import deque
from typing import Any, Optional

from pxnodes.llm.context.hierarchical_graph.layers import PlayerState


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
    max_depth: int = 1,
) -> list[Any]:
    """
    Perform forward BFS from target node for lookahead context.

    Args:
        target_node: The node to start from
        chart: The chart containing the nodes
        max_depth: Maximum depth to traverse (default 1 = immediate successors)

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

        if depth > max_depth:
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
        if depth < max_depth:
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


def aggregate_player_state(path_nodes: list[Any]) -> PlayerState:
    """
    Aggregate player state from traversing a path of nodes.

    Extracts items, mechanics, narrative beats from each node's
    components and description.

    Args:
        path_nodes: List of nodes in path order

    Returns:
        PlayerState with accumulated state
    """
    state = PlayerState()

    for node in path_nodes:
        # Check components for state-affecting values
        components = getattr(node, "components", None)
        if components:
            comp_list = components.all() if hasattr(components, "all") else []
            for comp in comp_list:
                definition = getattr(comp, "definition", None)
                if not definition:
                    continue

                def_name = getattr(definition, "name", "").lower()
                value = getattr(comp, "value", None)

                # Extract items/rewards
                if "item" in def_name or "reward" in def_name or "grants" in def_name:
                    if value:
                        state.items_collected.append(str(value))

                # Extract mechanics
                if "mechanic" in def_name or "ability" in def_name:
                    if value:
                        state.mechanics_unlocked.append(str(value))

                # Check for checkpoint
                if "checkpoint" in def_name or "save" in def_name:
                    node_name = getattr(node, "name", "Checkpoint")
                    state.checkpoints_passed.append(node_name)

        # Extract narrative from description (simplified)
        description = getattr(node, "description", "")
        if description:
            # Look for narrative indicators
            narrative_keywords = [
                "reveals",
                "discovers",
                "learns",
                "meets",
                "defeats",
                "unlocks",
            ]
            desc_lower = description.lower()
            for keyword in narrative_keywords:
                if keyword in desc_lower:
                    # Add truncated description as narrative beat
                    beat = description[:100] if len(description) > 100 else description
                    state.narrative_beats.append(beat)
                    break

    return state


def _find_container_for_node(node: Any, chart: Any) -> Optional[Any]:
    """Find the chart container that contains a given node."""
    containers = getattr(chart, "containers", None)
    if not containers:
        return None

    # Try to filter by content
    container_qs = (
        containers.filter(content=node) if hasattr(containers, "filter") else []
    )
    if container_qs:
        return container_qs.first() if hasattr(container_qs, "first") else None

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
