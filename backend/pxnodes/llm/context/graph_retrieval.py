"""
Graph slice retrieval for PX Charts.

Retrieves target node and its immediate neighbors (previous/next) from chart topology.
Based on the context building strategy in structural_context_strategy.md.
"""

from dataclasses import dataclass, field
from typing import Optional

from pxcharts.models import PxChart, PxChartContainer
from pxnodes.models import PxNode


@dataclass
class GraphSlice:
    """
    Represents a slice of the chart graph centered on a target node.

    Contains the target node and its immediate neighbors based on edge directions.
    """

    target: PxNode
    chart: PxChart
    previous_nodes: list[PxNode] = field(default_factory=list)
    next_nodes: list[PxNode] = field(default_factory=list)
    target_container: Optional[PxChartContainer] = None
    previous_containers: list[PxChartContainer] = field(default_factory=list)
    next_containers: list[PxChartContainer] = field(default_factory=list)

    @property
    def all_nodes(self) -> list[PxNode]:
        """Get all nodes in the slice (target + neighbors)."""
        return [self.target] + self.previous_nodes + self.next_nodes

    @property
    def all_containers(self) -> list[PxChartContainer]:
        """Get all containers in the slice."""
        containers = self.previous_containers + self.next_containers
        if self.target_container:
            containers = [self.target_container] + containers
        return containers


def get_graph_slice(
    target_node: PxNode,
    chart: PxChart,
    depth: int = 1,
) -> GraphSlice:
    """
    Retrieve a graph slice centered on the target node.

    Args:
        target_node: The node to center the slice on
        chart: The chart containing the node
        depth: How many levels of neighbors to include (default: 1 for immediate)

    Returns:
        GraphSlice containing target and neighbor nodes
    """
    slice_result = GraphSlice(target=target_node, chart=chart)

    # Find container(s) containing this node
    target_containers = list(chart.containers.filter(content=target_node))

    if not target_containers:
        # Node not in chart, return just the target
        return slice_result

    # Use first container as primary (nodes typically appear once in a chart)
    slice_result.target_container = target_containers[0]

    # Collect previous and next nodes
    previous_nodes_set: set[PxNode] = set()
    next_nodes_set: set[PxNode] = set()
    previous_containers: list[PxChartContainer] = []
    next_containers: list[PxChartContainer] = []

    for container in target_containers:
        # Previous nodes (incoming edges to this container)
        for edge in container.incoming_edges.select_related("source__content").all():
            if edge.source and edge.source.content:
                if edge.source.content != target_node:
                    previous_nodes_set.add(edge.source.content)
                    if edge.source not in previous_containers:
                        previous_containers.append(edge.source)

        # Next nodes (outgoing edges from this container)
        for edge in container.outgoing_edges.select_related("target__content").all():
            if edge.target and edge.target.content:
                if edge.target.content != target_node:
                    next_nodes_set.add(edge.target.content)
                    if edge.target not in next_containers:
                        next_containers.append(edge.target)

    slice_result.previous_nodes = list(previous_nodes_set)
    slice_result.next_nodes = list(next_nodes_set)
    slice_result.previous_containers = previous_containers
    slice_result.next_containers = next_containers

    # If depth > 1, recursively get neighbors of neighbors
    if depth > 1:
        for prev_node in list(slice_result.previous_nodes):
            deeper_slice = get_graph_slice(prev_node, chart, depth - 1)
            for n in deeper_slice.previous_nodes:
                if n not in previous_nodes_set and n != target_node:
                    slice_result.previous_nodes.append(n)
                    previous_nodes_set.add(n)

        for next_node in list(slice_result.next_nodes):
            deeper_slice = get_graph_slice(next_node, chart, depth - 1)
            for n in deeper_slice.next_nodes:
                if n not in next_nodes_set and n != target_node:
                    slice_result.next_nodes.append(n)
                    next_nodes_set.add(n)

    return slice_result


def get_node_position_in_chart(node: PxNode, chart: PxChart) -> Optional[int]:
    """
    Get the topological position of a node in the chart.

    Returns None if node not in chart, otherwise returns position index
    where 0 is the earliest node(s) with no incoming edges.
    """
    containers = list(chart.containers.filter(content=node))
    if not containers:
        return None

    container = containers[0]

    # Count how many edges we need to traverse backwards to reach a root
    visited: set[str] = set()

    def count_depth(c: PxChartContainer, depth: int) -> int:
        if str(c.id) in visited:
            return depth
        visited.add(str(c.id))

        max_depth = depth
        for edge in c.incoming_edges.select_related("source").all():
            if edge.source:
                parent_depth = count_depth(edge.source, depth + 1)
                max_depth = max(max_depth, parent_depth)

        return max_depth

    return count_depth(container, 0)


def get_all_paths_through_node(
    node: PxNode,
    chart: PxChart,
    max_length: int = 5,
) -> list[list[PxNode]]:
    """
    Get all paths through a node in the chart.

    Useful for analyzing the flow context around a node.
    """
    paths: list[list[PxNode]] = []

    containers = list(chart.containers.filter(content=node))
    if not containers:
        return paths

    container = containers[0]

    # Get backwards paths
    def get_backward_paths(
        c: PxChartContainer, path: list[PxNode], remaining: int
    ) -> list[list[PxNode]]:
        if remaining <= 0:
            return [path]

        backward_paths: list[list[PxNode]] = []
        has_incoming = False

        for edge in c.incoming_edges.select_related("source__content").all():
            if edge.source and edge.source.content:
                has_incoming = True
                new_path = [edge.source.content] + path
                backward_paths.extend(
                    get_backward_paths(edge.source, new_path, remaining - 1)
                )

        if not has_incoming:
            return [path]

        return backward_paths

    # Get forward paths
    def get_forward_paths(
        c: PxChartContainer, path: list[PxNode], remaining: int
    ) -> list[list[PxNode]]:
        if remaining <= 0:
            return [path]

        forward_paths: list[list[PxNode]] = []
        has_outgoing = False

        for edge in c.outgoing_edges.select_related("target__content").all():
            if edge.target and edge.target.content:
                has_outgoing = True
                new_path = path + [edge.target.content]
                forward_paths.extend(
                    get_forward_paths(edge.target, new_path, remaining - 1)
                )

        if not has_outgoing:
            return [path]

        return forward_paths

    # Combine backward and forward paths
    backward = get_backward_paths(container, [node], max_length // 2)
    forward = get_forward_paths(container, [node], max_length // 2)

    # Merge paths (remove duplicate center node)
    for back_path in backward:
        for fwd_path in forward:
            if len(fwd_path) > 1:
                combined = back_path + fwd_path[1:]  # Skip duplicate node
            else:
                combined = back_path
            if combined not in paths:
                paths.append(combined)

    return paths
