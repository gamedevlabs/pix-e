"""
Forward Coherence Agent.

Evaluates whether a node properly sets up future nodes across possible paths.
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import ForwardCoherenceResult

FORWARD_COHERENCE_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate FORWARD COHERENCE

Analyze whether the target node properly sets up what comes next
across all valid outgoing paths.

CHECK FOR:
1. MECHANICAL SETUP
   - If the node introduces mechanics, items, characters, or plot points, \
    are they used/referenced in a future node?

2. NARRATIVE SETUP
   - Do the story elements introduced in this node pay off later?
   - Is foreshadowing appropriate and not heavy-handed?
   - Example: NPC mentions a locked door player will encounter

4. WORLD BUILDING
   - Are locations/characters introduced properly?
   - Is context provided for future events?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "elements_introduced": ["New elements introduced in this node"]
- "potential_payoffs": ["How these elements might pay off later"]
"""
)


class ForwardCoherenceAgent(CoherenceDimensionAgent):
    """Evaluates whether a node properly sets up future content."""

    name = "forward_coherence"
    dimension_name = "Forward Coherence"
    response_schema = ForwardCoherenceResult
    prompt_template = FORWARD_COHERENCE_PROMPT
    temperature = 0

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build forward-specific context."""
        forward_nodes = data.get("forward_nodes", [])

        context_parts = []

        # Add forward path information
        if forward_nodes:
            context_parts.append(
                f"FORWARD PATH: {len(forward_nodes)} nodes follow this point"
            )
            node_names = [n.get("name", "Unknown") for n in forward_nodes[:5]]
            context_parts.append(f"Upcoming nodes: {' → '.join(node_names)}")

            # Extract requirements from forward nodes if available
            requirements = []
            for node in forward_nodes[:5]:
                if node.get("requires"):
                    requirements.extend(node.get("requires", []))
            if requirements:
                context_parts.append(
                    f"Future requirements: {', '.join(set(requirements))}"
                )

        return "\n".join(context_parts)
