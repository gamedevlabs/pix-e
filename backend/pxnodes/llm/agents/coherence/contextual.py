"""
Global Fit Agent.

Evaluates whether a node aligns with the game concept and pillars.
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import GlobalFitResult

GLOBAL_FIT_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate GLOBAL FIT

Analyze whether the target node aligns with the overall game concept, pillars,
tone, and genre expectations.

CHECK FOR:
1. PILLAR ALIGNMENT
   - Does the node reinforce or conflict with the stated design pillars?
   - Are there explicit violations (e.g., non-violent pillar vs combat-only node)?

2. CONCEPT ALIGNMENT
   - Is the node consistent with the game's concept, genre, and tone?
   - Does it introduce themes or mechanics that contradict the core premise?

3. WORLD/TONE CONSISTENCY
   - Does the node fit the established world and narrative tone?
   - Are characters/locations consistent with the setting?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "pillar_alignment": ["How the node aligns or conflicts with each pillar"]
- "concept_alignment": "Overall alignment with the game concept and tone"
"""
)


class GlobalFitAgent(CoherenceDimensionAgent):
    """Evaluates whether a node aligns with concept and pillars."""

    name = "global_fit"
    dimension_name = "Global Fit"
    response_schema = GlobalFitResult
    prompt_template = GLOBAL_FIT_PROMPT
    temperature = 0

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build global fit context."""
        pillars = data.get("pillars", [])
        game_concept = data.get("game_concept")

        context_parts = []

        if game_concept:
            concept_text = getattr(game_concept, "content", "") or ""
            if concept_text:
                context_parts.append("GAME CONCEPT:")
                context_parts.append(concept_text)

        if pillars:
            context_parts.append("DESIGN PILLARS:")
            for pillar in pillars:
                name = pillar.get("name", "Pillar")
                description = pillar.get("description", "")
                context_parts.append(f"- {name}: {description}")

        return (
            "\n".join(context_parts) if context_parts else "No global context provided"
        )
