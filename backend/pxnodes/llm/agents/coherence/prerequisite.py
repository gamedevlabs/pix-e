"""
Backward Coherence Agent.

Evaluates whether a node respects what came before across possible paths.
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import BackwardCoherenceResult

BACKWARD_COHERENCE_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate BACKWARD COHERENCE

Analyze whether the target node properly respects what came before
across all valid predecessor paths.

CHECK FOR:
1. REQUIRED MECHANICS/ITEMS
   - Does the node require mechanics or items that appear earlier?
   - Are they established on ALL valid incoming paths?
   - If only on some paths, flag as path-dependent.
   - Treat explicit action/knowledge verbs as requirements (e.g., "uses", \
    "accesses", "knows how to", "has learned"). If the \
    exact mechanic/knowledge is not introduced earlier, mark it missing.

2. NARRATIVE PREREQUISITES
   - Does the node reference events that have occurred?
   - Are character introductions properly sequenced?
   - Example violation: "Return to the castle" but player never visited it

3. STATE PREREQUISITES
   - Does the node assume a game state that is achievable on all paths?
   - Are triggers/conditions for reaching this node satisfiable on all paths?

PROCESS (strict):
1) Extract REQUIRED mechanics/items/knowledge from the TARGET NODE details.
2) For each requirement, find an explicit quote in PREVIOUS NODES only.
3) If no explicit quote exists, list it under "missing_prerequisites".
4) Do not use the TARGET NODE as evidence.

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


class BackwardCoherenceAgent(CoherenceDimensionAgent):
    """Evaluates whether a node respects what came before."""

    name = "backward_coherence"
    dimension_name = "Backward Coherence"
    response_schema = BackwardCoherenceResult
    prompt_template = BACKWARD_COHERENCE_PROMPT
    temperature = 0

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

        return "\n".join(context_parts)
