"""
Unique Features agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.unique_features import UNIQUE_FEATURES_PROMPT


class UniqueFeaturesAgentV2(AspectAgentV2):
    """Evaluates unique features definition."""

    name = "unique_features_v2"
    aspect_name = "unique_features"
    prompt_template = UNIQUE_FEATURES_PROMPT
    temperature = 0.4  # Slightly more creative

    def _get_default_suggestions(self) -> List[str]:
        return [
            "Identify what makes your game unique.",
            "Explain how it differs from similar games.",
            "List 3-5 defining elements that set it apart.",
        ]
