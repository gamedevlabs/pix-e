"""
SPARC V2 prompts.

Focused prompts for router-based agentic evaluation.
"""

from sparc.llm.prompts.v2.art_direction import ART_DIRECTION_PROMPT
from sparc.llm.prompts.v2.gameplay import GAMEPLAY_PROMPT
from sparc.llm.prompts.v2.goals_challenges import GOALS_CHALLENGES_REWARDS_PROMPT
from sparc.llm.prompts.v2.opportunities_risks import OPPORTUNITIES_RISKS_PROMPT
from sparc.llm.prompts.v2.place import PLACE_PROMPT
from sparc.llm.prompts.v2.player_experience import PLAYER_EXPERIENCE_PROMPT
from sparc.llm.prompts.v2.purpose import PURPOSE_PROMPT
from sparc.llm.prompts.v2.router import ROUTER_PROMPT
from sparc.llm.prompts.v2.story_narrative import STORY_NARRATIVE_PROMPT
from sparc.llm.prompts.v2.synthesis import SYNTHESIS_PROMPT
from sparc.llm.prompts.v2.theme import THEME_PROMPT
from sparc.llm.prompts.v2.unique_features import UNIQUE_FEATURES_PROMPT

__all__ = [
    "ROUTER_PROMPT",
    "PLAYER_EXPERIENCE_PROMPT",
    "THEME_PROMPT",
    "PURPOSE_PROMPT",
    "GAMEPLAY_PROMPT",
    "GOALS_CHALLENGES_REWARDS_PROMPT",
    "PLACE_PROMPT",
    "STORY_NARRATIVE_PROMPT",
    "UNIQUE_FEATURES_PROMPT",
    "ART_DIRECTION_PROMPT",
    "OPPORTUNITIES_RISKS_PROMPT",
    "SYNTHESIS_PROMPT",
]
