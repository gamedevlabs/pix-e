"""
Goals, Challenges & Rewards agent for SPARC V2.
"""

from typing import List

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.goals_challenges import GOALS_CHALLENGES_REWARDS_PROMPT


class GoalsChallengesRewardsAgentV2(AspectAgentV2):
    """Evaluates goals, challenges, and rewards definition."""

    name = "goals_challenges_rewards_v2"
    aspect_name = "goals_challenges_rewards"
    prompt_template = GOALS_CHALLENGES_REWARDS_PROMPT

    def _get_default_suggestions(self) -> List[str]:
        return [
            "List the objectives players must complete.",
            "Define obstacles and challenges for each objective.",
            "Describe rewards for completing objectives.",
            "Plan how to communicate objectives to players.",
        ]
