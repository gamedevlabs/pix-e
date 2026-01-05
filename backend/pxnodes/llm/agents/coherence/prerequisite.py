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

EVIDENCE RULES (backward coherence):
- The TARGET NODE text is not evidence of prior acquisition; it only defines \
requirements.
- You may only cite PREVIOUS NODES as evidence for prerequisites. Do not \
cite the target node or future nodes.
- Any item in "satisfied_prerequisites" must include a quoted fragment from \
previous node descriptions.
- A prerequisite cannot be both "missing_prerequisites" and \
"satisfied_prerequisites". If evidence is absent or invalid, it must be \
missing.

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

PREREQUISITE CHECKLIST:
1) Extract required mechanics/items/abilities from the TARGET NODE text.
2) For each requirement, find explicit evidence in PREVIOUS NODES only.
3) If no quote exists, mark it as missing (do not invent evidence).

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
        """Build prerequisite-specific context.

        Note: Path listings are already included in the filtered context from
        _filter_trace_content(), so we only add summary info here.
        """
        backward_nodes = data.get("backward_nodes", [])
        backward_paths = data.get("backward_paths", [])

        context_parts = []

        # Add backward node pool summary (paths are in filtered context)
        if backward_nodes:
            context_parts.append(
                f"POOL OF PRIOR NODES: {len(backward_nodes)} nodes can lead to "
                "this point"
            )

        if backward_paths:
            context_parts.append(f"({len(backward_paths)} paths to target)")

        return "\n".join(context_parts)
