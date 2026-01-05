"""
Layer building functions for Hierarchical Graph strategy.

Implements the 4-layer hierarchy from the user's H-MEM adaptation:
- L1 Domain: Project-level (Pillars + Game Concept)
- L2 Category: Chart-level (Arc summary, pacing)
- L3 Trace: Path-level (Pool of nodes + explicit paths)
- L4 Episode: Node-level (Atomic node details)
"""

from typing import Any, Optional

from pxnodes.llm.context.base.types import LayerContext, get_layer_name


def build_domain_layer(
    project_pillars: Optional[list] = None,
    game_concept: Optional[Any] = None,
) -> LayerContext:
    """
    Build L1 Domain layer from project-level context.

    Content includes:
    - Design Pillars (the "North Star" of the project)
    - Game Concept (SPARC evaluation summary)

    Evaluation question: "Does the Node match the pillars and game concept?"

    NOTE: No arbitrary truncation - project context should be preserved in full.
    """
    content_parts = []

    # Game Concept - FULL content, no truncation
    if game_concept:
        concept_text = getattr(game_concept, "content", str(game_concept))
        content_parts.append(f"Game Concept:\n{concept_text}")

    # Design Pillars - ALL pillars with FULL descriptions
    if project_pillars:
        pillars_text = []
        for pillar in project_pillars:  # All pillars, not limited
            name = getattr(pillar, "name", str(pillar))
            desc = getattr(pillar, "description", "")
            if desc:
                pillars_text.append(f"- {name}: {desc}")  # Full description
            else:
                pillars_text.append(f"- {name}")
        content_parts.append("Design Pillars:\n" + "\n".join(pillars_text))

    if not content_parts:
        content_parts.append("No project-level context available.")

    return LayerContext(
        layer=1,
        layer_name=get_layer_name(1),
        content="\n\n".join(content_parts),
        metadata={
            "source": "project_config",
            "has_pillars": project_pillars is not None,
            "has_concept": game_concept is not None,
            "pillar_count": len(project_pillars) if project_pillars else 0,
        },
    )


def build_category_layer(
    chart: Any,
    include_summary: bool = True,
) -> LayerContext:
    """
    Build L2 Category layer from chart context.

    Content includes:
    - Chart name and description
    - Arc summary (pacing, tone expectations)

    Evaluation question: "Does the Node make sense in the context of the Chart?"
    """
    chart_name = getattr(chart, "name", "Unknown Chart")
    chart_description = getattr(chart, "description", None)

    content_parts = [f"Chart: {chart_name}"]

    if chart_description:
        content_parts.append(f"Description: {chart_description}")

    # Compute chart-level metrics if containers available
    containers = getattr(chart, "containers", None)
    if containers:
        container_count = containers.count() if hasattr(containers, "count") else 0
        content_parts.append(f"Total Nodes: {container_count}")

    return LayerContext(
        layer=2,
        layer_name=get_layer_name(2),
        content="\n".join(content_parts),
        metadata={
            "chart_id": str(getattr(chart, "id", "")),
            "chart_name": chart_name,
        },
    )


def _format_node_for_trace(node: Any, index: int) -> str:
    """Format a single node for trace display with full content."""
    name = getattr(node, "name", f"Node {index}")
    description = getattr(node, "description", "")

    parts = [f"  {index}. {name}:"]

    if description:
        parts.append(f"     {description}")

    # Include component values
    components = getattr(node, "components", None)
    if components:
        comp_list = components.all() if hasattr(components, "all") else list(components)
        comp_strs = []
        for comp in comp_list:
            def_name = getattr(getattr(comp, "definition", None), "name", "")
            value = getattr(comp, "value", "")
            if def_name and value is not None:
                comp_strs.append(f"{def_name}={value}")
        if comp_strs:
            parts.append(f"     [{', '.join(comp_strs)}]")

    return "\n".join(parts)


def _format_paths(paths: list[list[Any]], direction: str) -> str:
    """
    Format a list of paths for display.

    Args:
        paths: List of paths, each path is a list of nodes
        direction: "backward" or "forward" for appropriate empty message

    Returns:
        Formatted string with numbered paths
    """
    if not paths:
        if direction == "backward":
            return "  None (this is the start of the flow)"
        else:
            return "  None (this is the end of the flow)"

    lines = []
    for i, path in enumerate(paths, 1):
        path_names = [getattr(node, "name", f"Node {j}") for j, node in enumerate(path)]
        lines.append(f"  {i}. {' -> '.join(path_names)}")
    return "\n".join(lines)


def build_trace_layer(
    backward_nodes: list[Any],
    target_node: Any,
    forward_nodes: Optional[list[Any]] = None,
    backward_paths: Optional[list[list[Any]]] = None,
    forward_paths: Optional[list[list[Any]]] = None,
) -> LayerContext:
    """
    Build L3 Trace layer from path traversal.

    Content includes:
    - POOL OF ALL PRIOR NODES: All nodes that can lead to target
    - ALL POSSIBLE PATHS TO TARGET: Explicit enumeration of paths
    - POOL OF ALL FUTURE NODES: All nodes reachable from target
    - ALL POSSIBLE PATHS FROM TARGET: Explicit enumeration of paths

    For coherence checking, we need both backward AND forward context
    to verify prerequisites and ensure proper setup for future nodes.

    Evaluation question: "Does the node work in the context of its Path?"
    """
    content_parts = []

    # POOL OF ALL PRIOR NODES - with full content
    if backward_nodes:
        content_parts.append("POOL OF ALL PRIOR NODES (nodes that can lead to target):")
        for i, node in enumerate(backward_nodes, 1):
            content_parts.append(_format_node_for_trace(node, i))
    else:
        content_parts.append(
            "POOL OF ALL PRIOR NODES: None (this is the start of the flow)"
        )

    # ALL POSSIBLE PATHS TO TARGET
    content_parts.append("\nALL POSSIBLE PATHS TO TARGET:")
    content_parts.append(_format_paths(backward_paths or [], "backward"))

    # POOL OF ALL FUTURE NODES - with full content
    if forward_nodes:
        content_parts.append(
            "\nPOOL OF ALL FUTURE NODES (nodes reachable from target):"
        )
        for i, node in enumerate(forward_nodes, 1):
            content_parts.append(_format_node_for_trace(node, i))
    else:
        content_parts.append(
            "\nPOOL OF ALL FUTURE NODES: None (this is the end of the flow)"
        )

    # ALL POSSIBLE PATHS FROM TARGET
    content_parts.append("\nALL POSSIBLE PATHS FROM TARGET:")
    content_parts.append(_format_paths(forward_paths or [], "forward"))

    return LayerContext(
        layer=3,
        layer_name=get_layer_name(3),
        content="\n".join(content_parts) if content_parts else "No path context",
        metadata={
            "backward_node_count": len(backward_nodes),
            "forward_node_count": len(forward_nodes) if forward_nodes else 0,
            "backward_path_count": len(backward_paths) if backward_paths else 0,
            "forward_path_count": len(forward_paths) if forward_paths else 0,
            "target_node_id": str(getattr(target_node, "id", "")),
        },
    )


def build_episode_layer(
    node: Any,
    include_components: bool = True,
) -> LayerContext:
    """
    Build L4 Episode layer from target node.

    Content includes:
    - Node title and description
    - Component values (intensity, category, etc.)

    Evaluation question: "Is the Node coherent in a vacuum?"
    """
    node_id = str(getattr(node, "id", "unknown"))
    node_name = getattr(node, "name", "Unknown Node")
    node_description = getattr(node, "description", None)

    content_parts = [
        f"Node ID: {node_id}",
        f"Title: {node_name}",
    ]

    if node_description:
        content_parts.append(f"Description: {node_description}")

    # Include component values
    if include_components:
        components = getattr(node, "components", None)
        if components:
            component_list = (
                components.all() if hasattr(components, "all") else list(components)
            )
            for comp in component_list:
                def_name = getattr(
                    getattr(comp, "definition", None), "name", "Component"
                )
                value = getattr(comp, "value", "N/A")
                content_parts.append(f"- {def_name}: {value}")

    return LayerContext(
        layer=4,
        layer_name=get_layer_name(4),
        content="\n".join(content_parts),
        metadata={
            "node_id": node_id,
            "node_name": node_name,
            "has_description": node_description is not None,
        },
    )
