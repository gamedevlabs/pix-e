"""
Forward Setup Agent.

Evaluates whether a node properly sets up future nodes:
- Are elements introduced that will be used later?
- Is foreshadowing appropriate?
- Are mechanics taught before being required?
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import ForwardSetupResult

FORWARD_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate FORWARD SETUP

Analyze whether the target node properly sets up what comes next in the game flow.

CHECK FOR:
1. MECHANICAL SETUP
   - Does the node introduce mechanics that will be needed later?
   - Are abilities/items granted that enable future progression?
   - Example: Tutorial teaches wall-jump before wall-jump puzzle

2. NARRATIVE SETUP
   - Are story elements introduced that pay off later?
   - Is foreshadowing appropriate and not heavy-handed?
   - Example: NPC mentions a locked door player will encounter

3. DIFFICULTY RAMP
   - Does the node prepare player for upcoming challenges?
   - Is the skill progression appropriate?
   - Example: Easy enemies before boss teach attack patterns

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


class ForwardSetupAgent(CoherenceDimensionAgent):
    """Evaluates whether a node properly sets up future content."""

    name = "forward_setup"
    dimension_name = "Forward Setup"
    response_schema = ForwardSetupResult
    prompt_template = FORWARD_PROMPT
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
