"""
Internal Consistency Agent.

Evaluates whether a node is internally coherent:
- Are there contradictions within the node?
- Are descriptions clear and unambiguous?
- Do the components work together logically?
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import InternalConsistencyResult

INTERNAL_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate INTERNAL CONSISTENCY

Analyze whether the target node is internally coherent and well-defined.

CHECK FOR:
1. CONTRADICTIONS
   - Do different parts of the node contradict each other?
   - Does the description match the node type/category?
   - Example: "Calm exploration" with Tension=95

2. CLARITY
   - Is the node's purpose clear?
   - Are descriptions specific enough to implement?
   - Example violation: "Do the thing with the stuff"

3. COMPONENT HARMONY
   - Do all node components work together?
   - Is the component category and value appropriate for the content?
   - Are visual/audio hints consistent with the experience?

4. COMPLETENESS
   - Is all necessary information present?
   - Are edge cases considered?
   - Are player choices well-defined?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "contradictions": ["List of internal contradictions found"]
- "unclear_elements": ["Vague or unclear elements that need clarification"]
"""
)


class InternalConsistencyAgent(CoherenceDimensionAgent):
    """Evaluates whether a node is internally coherent."""

    name = "internal_consistency"
    dimension_name = "Internal Consistency"
    response_schema = InternalConsistencyResult
    prompt_template = INTERNAL_PROMPT
    temperature = 0

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build internal-specific context."""
        node_details = data.get("node_details", {})

        context_parts = []

        # Add node component details
        if node_details:
            if node_details.get("category"):
                context_parts.append(f"Category: {node_details['category']}")
            if node_details.get("components"):
                components = node_details["components"]
                context_parts.append(f"Components: {len(components)} defined")
                for comp in components[:5]:
                    if isinstance(comp, dict):
                        name = comp.get("name", "Unknown")
                        value = comp.get("value", "")
                        context_parts.append(f"  - {name}: {value}")

        return (
            "\n".join(context_parts) if context_parts else "No additional node details"
        )
