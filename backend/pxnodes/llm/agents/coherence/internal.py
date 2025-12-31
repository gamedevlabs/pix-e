"""
Node Integrity Agent.

Evaluates whether a node is internally coherent:
- Do title, description, and components align?
- Are descriptions clear and implementable?
- Are there contradictions or missing details?
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import NodeIntegrityResult

INTEGRITY_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate NODE INTEGRITY

Analyze whether the target node is internally coherent and well-defined.

EVIDENCE RULES (node integrity):
- Use only the TARGET NODE DETAILS (title/description/components).

CHECK FOR:
1. CONTRADICTIONS
   - Do different parts of the node contradict each other?
   - Does the title match the description?
   - If there are components, does the description match the node components?
   - Does a part of the node description contradict another part of the
     node description?
   - Example: "Calm exploration" with Tension=95

2. CLARITY
   - Is the node's purpose clear?
   - Are descriptions specific enough to implement?
   - Example violation: "Do the thing with the stuff"

3. COMPONENT HARMONY
   - Do all node components work together?
   - Is the component category and value appropriate for the content?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "contradictions": ["List of internal contradictions found"]
- "unclear_elements": ["Vague or unclear elements that need clarification"]
"""
)


class NodeIntegrityAgent(CoherenceDimensionAgent):
    """Evaluates whether a node is internally coherent."""

    name = "node_integrity"
    dimension_name = "Node Integrity"
    response_schema = NodeIntegrityResult
    prompt_template = INTEGRITY_PROMPT
    temperature = 0

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build internal-specific context."""
        return ""
