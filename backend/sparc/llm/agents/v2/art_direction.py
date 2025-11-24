"""
Art Direction agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.art_direction import ART_DIRECTION_PROMPT


class ArtDirectionAgentV2(AspectAgentV2):
    """Evaluates art direction definition."""

    name = "art_direction_v2"
    aspect_name = "art_direction"
    prompt_template = ART_DIRECTION_PROMPT
    temperature = 0.4  # Slightly more creative

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Specify the art style (realistic, stylized, cartoonish, etc.).",
            "Define the color palette (primary, secondary, light/shadow).",
            "Describe lighting and atmosphere.",
            "Gather visual references and create a mood board.",
        ]
