"""
Player Experience agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.player_experience import PLAYER_EXPERIENCE_PROMPT


class PlayerExperienceAgentV2(AspectAgentV2):
    """Evaluates player experience definition."""

    name = "player_experience_v2"
    aspect_name = "player_experience"
    prompt_template = PLAYER_EXPERIENCE_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Describe the player experience from the player's perspective "
            "using active form.",
            "Focus on emotional keywords: what should players FEEL?",
            "Create a 1-2 sentence high concept statement.",
        ]
