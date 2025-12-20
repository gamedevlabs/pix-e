"""
Contextual Fit Agent.

Evaluates whether a node fits the broader game context:
- Does it align with design pillars?
- Does it fit the overall game concept?
- Is it consistent with the game's tone and style?
"""

from typing import Any, Dict

from pxnodes.llm.agents.coherence.base import (
    COHERENCE_CONTEXT_HEADER,
    SCORING_INSTRUCTIONS,
    CoherenceDimensionAgent,
)
from pxnodes.llm.agents.coherence.schemas import ContextualFitResult

CONTEXTUAL_PROMPT = (
    COHERENCE_CONTEXT_HEADER
    + """
TASK: Evaluate CONTEXTUAL FIT

Analyze whether the target node fits the broader game context and design vision.

CHECK FOR:
1. PILLAR ALIGNMENT
   - Does the node support the game's design pillars?
   - Are there conflicts with stated design goals?
   - Example: Pillar is "Non-violent conflict resolution" but node has combat

2. CONCEPT ALIGNMENT
   - Does the node fit the overall game concept?
   - Is it consistent with the game's genre and target audience?
   - Example: Gritty realistic shooter with cartoon powerups

3. TONE CONSISTENCY
   - Does the node match the game's tone?
   - Is the writing style consistent?
   - Example: Dark horror game with comedic dialogue

4. STYLE COHERENCE
   - Do visual/audio directions fit the game's aesthetic?
   - Are gameplay elements consistent with the genre?

"""
    + SCORING_INSTRUCTIONS
    + """
ADDITIONAL FIELDS:
- "pillar_alignment": ["How the node aligns (or conflicts) with each pillar"]
- "concept_alignment": "Overall assessment of fit with game concept"
"""
)


class ContextualFitAgent(CoherenceDimensionAgent):
    """Evaluates whether a node fits the broader game context."""

    name = "contextual_fit"
    dimension_name = "Contextual Fit"
    response_schema = ContextualFitResult
    prompt_template = CONTEXTUAL_PROMPT
    temperature = 0.3

    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """Build contextual-specific context."""
        pillars = data.get("pillars", [])
        game_concept = data.get("game_concept", "")

        context_parts = []

        # Add pillar information
        if pillars:
            context_parts.append(f"DESIGN PILLARS ({len(pillars)} defined):")
            for pillar in pillars[:6]:  # Limit to 6 pillars
                if isinstance(pillar, dict):
                    name = pillar.get("name", "Unknown")
                    desc = pillar.get("description", "")
                    context_parts.append(f"  - {name}: {desc[:100]}")
                elif hasattr(pillar, "name"):
                    context_parts.append(
                        f"  - {pillar.name}: {getattr(pillar, 'description', '')[:100]}"
                    )

        # Add game concept
        if game_concept:
            concept_text = game_concept
            if hasattr(game_concept, "content"):
                concept_text = game_concept.content
            context_parts.append(f"\nGAME CONCEPT:\n{concept_text[:500]}")

        return (
            "\n".join(context_parts)
            if context_parts
            else "No pillars or game concept provided"
        )
