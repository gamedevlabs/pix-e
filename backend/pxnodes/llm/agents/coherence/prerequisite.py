"""
Prerequisite Alignment Agent.

Evaluates whether a node respects what came before in the game flow:
- Are required items/abilities established?
- Are referenced events/mechanics already introduced?
- Are prerequisite conditions satisfied?
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import PrerequisiteAlignmentResult

PREREQUISITE_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate PREREQUISITE ALIGNMENT

Analyze whether the target node properly respects what came before in the game flow.

CHECK FOR:
1. ITEM/ABILITY PREREQUISITES
   - Does the node require items/abilities the player should have?
   - Are all required mechanics already introduced?
   - Example violation: "Use Double Jump" but player never acquired it

2. NARRATIVE PREREQUISITES
   - Does the node reference events that have occurred?
   - Are character introductions properly sequenced?
   - Example violation: "Return to the castle" but player never visited it

3. MECHANICAL PREREQUISITES
   - Are gameplay mechanics properly introduced before use?
   - Is complexity appropriately ramped up?
   - Example violation: Complex combo required without tutorial

4. STATE PREREQUISITES
   - Does the node assume a game state that is achievable?
   - Are triggers/conditions for reaching this node satisfiable?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "missing_prerequisites": [
    "List items/abilities/mechanics that are required but not established"
]
- "satisfied_prerequisites": [
    "List prerequisites that ARE properly established"
]
"""
)


class PrerequisiteAlignmentAgent(CoherenceDimensionAgent):
    """Evaluates whether a node respects what came before."""

    name = "prerequisite_alignment"
    dimension_name = "Prerequisite Alignment"
    response_schema = PrerequisiteAlignmentResult
    prompt_template = PREREQUISITE_PROMPT
    temperature = 0.3

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build prerequisite-specific context."""
        backward_nodes = data.get("backward_nodes", [])
        player_state = data.get("player_state", {})

        context_parts = []

        # Add backward path information
        if backward_nodes:
            context_parts.append(
                f"BACKWARD PATH: {len(backward_nodes)} nodes lead to this point"
            )
            node_names = [n.get("name", "Unknown") for n in backward_nodes[:5]]
            context_parts.append(f"Recent path: {' → '.join(node_names)}")

        # Add accumulated player state
        if player_state:
            items = player_state.get("items", [])
            mechanics = player_state.get("mechanics", [])
            if items:
                context_parts.append(f"Player has items: {', '.join(items)}")
            if mechanics:
                context_parts.append(f"Unlocked mechanics: {', '.join(mechanics)}")

        return "\n".join(context_parts) if context_parts else "No additional context"
