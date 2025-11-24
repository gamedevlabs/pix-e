"""
Gameplay agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.gameplay import GAMEPLAY_PROMPT


class GameplayAgentV2(AspectAgentV2):
    """Evaluates gameplay definition."""

    name = "gameplay_v2"
    aspect_name = "gameplay"
    prompt_template = GAMEPLAY_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "List 3-5 core verbs that describe player actions.",
            "Describe the core mechanics players interact with.",
            "Define the 30-second gameplay loop.",
        ]
