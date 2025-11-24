"""
Opportunities & Risks agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.opportunities_risks import OPPORTUNITIES_RISKS_PROMPT


class OpportunitiesRisksAgentV2(AspectAgentV2):
    """Evaluates opportunities and risks definition."""

    name = "opportunities_risks_v2"
    aspect_name = "opportunities_risks"
    prompt_template = OPPORTUNITIES_RISKS_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "List opportunities and how to leverage them.",
            "Identify potential risks and their likelihood.",
            "Describe mitigation strategies for each risk.",
        ]
