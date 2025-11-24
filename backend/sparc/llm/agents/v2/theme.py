"""
Theme agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.theme import THEME_PROMPT


class ThemeAgentV2(AspectAgentV2):
    """Evaluates theme definition."""

    name = "theme_v2"
    aspect_name = "theme"
    prompt_template = THEME_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Define the dominant, unifying theme of your game.",
            "Identify secondary themes that complement the main theme.",
            "Consider how themes connect to gameplay and narrative.",
        ]
