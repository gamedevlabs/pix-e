"""
Place agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.place import PLACE_PROMPT


class PlaceAgentV2(AspectAgentV2):
    """Evaluates place/setting definition."""

    name = "place_v2"
    aspect_name = "place"
    prompt_template = PLACE_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Define the environment setting and world type.",
            "List concrete key locations with specific names.",
            "Describe the atmosphere and feel of each location.",
        ]
