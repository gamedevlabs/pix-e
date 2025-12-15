"""
Layer building functions for Hierarchical Graph strategy.

Implements the 4-layer hierarchy from the user's H-MEM adaptation:
- L1 Domain: Project-level (Pillars + Game Concept)
- L2 Category: Chart-level (Arc summary, pacing)
- L3 Trace: Path-level (State accumulation via graph traversal)
- L4 Episode: Node-level (Atomic node details)
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from pxnodes.llm.context.base.types import LayerContext, get_layer_name


@dataclass
class PlayerState:
    """Accumulated player state from traversing the path."""

    items_collected: list[str] = field(default_factory=list)
    mechanics_unlocked: list[str] = field(default_factory=list)
    narrative_beats: list[str] = field(default_factory=list)
    checkpoints_passed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert to dictionary."""
        return {
            "items_collected": self.items_collected,
            "mechanics_unlocked": self.mechanics_unlocked,
            "narrative_beats": self.narrative_beats,
            "checkpoints_passed": self.checkpoints_passed,
        }


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


def build_trace_layer(
    path_nodes: list[Any],
    player_state: PlayerState,
    target_node: Any,
    forward_nodes: Optional[list[Any]] = None,
) -> LayerContext:
    """
    Build L3 Trace layer from path traversal.

    Content includes:
    - PREVIOUS nodes: Full content of nodes leading to target
    - FUTURE nodes: Full content of nodes after target
    - Player state (accumulated items, mechanics, narrative)

    For coherence checking, we need both backward AND forward context
    to verify prerequisites and ensure proper setup for future nodes.

    Evaluation question: "Does the node work in the context of its Path?"
    """
    content_parts = []

    # PREVIOUS NODES - with full content
    if path_nodes:
        content_parts.append("PREVIOUS NODES (Path leading to target):")
        for i, node in enumerate(path_nodes, 1):
            content_parts.append(_format_node_for_trace(node, i))
    else:
        content_parts.append("PREVIOUS NODES: None (this is the start of the path)")

    # FUTURE NODES - with full content
    if forward_nodes:
        content_parts.append("\nFUTURE NODES (What comes after target):")
        for i, node in enumerate(forward_nodes, 1):
            content_parts.append(_format_node_for_trace(node, i))
    else:
        content_parts.append("\nFUTURE NODES: None (this is the end of the path)")

    # Player state (accumulated from backward path)
    state_parts = []
    if player_state.items_collected:
        state_parts.append(f"Items: {', '.join(player_state.items_collected)}")
    if player_state.mechanics_unlocked:
        state_parts.append(f"Mechanics: {', '.join(player_state.mechanics_unlocked)}")
    if player_state.narrative_beats:
        state_parts.append(f"Narrative: {'; '.join(player_state.narrative_beats)}")
    if player_state.checkpoints_passed:
        state_parts.append(f"Checkpoints: {', '.join(player_state.checkpoints_passed)}")

    if state_parts:
        content_parts.append("\nACCUMULATED PLAYER STATE:")
        content_parts.extend([f"  - {s}" for s in state_parts])

    return LayerContext(
        layer=3,
        layer_name=get_layer_name(3),
        content="\n".join(content_parts) if content_parts else "No path context",
        metadata={
            "backward_count": len(path_nodes),
            "forward_count": len(forward_nodes) if forward_nodes else 0,
            "target_node_id": str(getattr(target_node, "id", "")),
            "player_state": player_state.to_dict(),
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
