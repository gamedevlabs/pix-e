"""
Story & Narrative agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.story_narrative import STORY_NARRATIVE_PROMPT


class StoryNarrativeAgentV2(AspectAgentV2):
    """Evaluates story and narrative definition."""

    name = "story_narrative_v2"
    aspect_name = "story_narrative"
    prompt_template = STORY_NARRATIVE_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Describe the story of the game or level.",
            "Explain what happened before the player arrived.",
            "Define how and why the player arrives at this place.",
            "Plan storytelling methods (environmental, dialogue, etc.).",
        ]
