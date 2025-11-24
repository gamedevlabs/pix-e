"""
Purpose agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.purpose import PURPOSE_PROMPT


class PurposeAgentV2(AspectAgentV2):
    """Evaluates purpose definition."""

    name = "purpose_v2"
    aspect_name = "purpose"
    prompt_template = PURPOSE_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "State the purpose of this project clearly.",
            "Explain why YOU want to work on this project.",
            "Define what you want to achieve by completing this project.",
        ]
