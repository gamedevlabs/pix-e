"""
Path Robustness Agent.

Evaluates whether a node works across incoming and outgoing paths.
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import PathRobustnessResult

PATH_ROBUSTNESS_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate PATH ROBUSTNESS

Analyze whether the target node makes sense across incoming and outgoing paths.

CHECK FOR:
1. CROSS-PATH CONSISTENCY
   - Does the node assume prerequisites that are missing on some paths?
   - Are its outcomes compatible with all likely successors?

2. BRANCH COMPATIBILITY
   - If multiple predecessors exist, does the node still make sense?
   - If multiple successors exist, does it set them up coherently?

3. PATH-SPECIFIC DEPENDENCIES
   - Identify any requirements that only hold on certain paths.

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "path_dependencies": ["Path-specific requirements or assumptions"]
- "robust_paths": ["Paths where the node fits cleanly"]
- "fragile_paths": ["Paths where the node conflicts or breaks"]
"""
)


class PathRobustnessAgent(CoherenceDimensionAgent):
    """Evaluates whether a node works across paths."""

    name = "path_robustness"
    dimension_name = "Path Robustness"
    response_schema = PathRobustnessResult
    prompt_template = PATH_ROBUSTNESS_PROMPT
    temperature = 0

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build path robustness context."""
        backward_nodes = data.get("backward_nodes", [])
        forward_nodes = data.get("forward_nodes", [])

        context_parts = []

        if backward_nodes:
            node_names = [n.get("name", "Unknown") for n in backward_nodes[:8]]
            context_parts.append(
                f"INCOMING CONTEXT ({len(backward_nodes)} nodes): "
                + " → ".join(node_names)
            )

        if forward_nodes:
            node_names = [n.get("name", "Unknown") for n in forward_nodes[:8]]
            context_parts.append(
                f"OUTGOING CONTEXT ({len(forward_nodes)} nodes): "
                + " → ".join(node_names)
            )

        return "\n".join(context_parts) if context_parts else "No path context provided"
