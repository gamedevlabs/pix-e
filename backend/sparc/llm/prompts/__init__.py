"""
SPARC prompt templates.

Re-exports all prompts for easy importing.
"""

# Gameplay prompts
from sparc.llm.prompts.gameplay import (
    GAMEPLAY_PROMPT,
    GOALS_CHALLENGES_REWARDS_PROMPT,
)

# Monolithic baseline prompt
from sparc.llm.prompts.monolithic import MONOLITHIC_SPARC_PROMPT

# Player-focused prompts
from sparc.llm.prompts.player_experience import (
    PLAYER_EXPERIENCE_PROMPT,
    PURPOSE_PROMPT,
    THEME_PROMPT,
)

# Visual and meta prompts
from sparc.llm.prompts.visual_meta import (
    ART_DIRECTION_PROMPT,
    OPPORTUNITIES_RISKS_PROMPT,
    UNIQUE_FEATURES_PROMPT,
)

# World-building prompts
from sparc.llm.prompts.world import PLACE_PROMPT, STORY_NARRATIVE_PROMPT

__all__ = [
    # Player-focused
    "PLAYER_EXPERIENCE_PROMPT",
    "THEME_PROMPT",
    "PURPOSE_PROMPT",
    # Gameplay
    "GAMEPLAY_PROMPT",
    "GOALS_CHALLENGES_REWARDS_PROMPT",
    # World-building
    "PLACE_PROMPT",
    "STORY_NARRATIVE_PROMPT",
    # Visual and meta
    "ART_DIRECTION_PROMPT",
    "UNIQUE_FEATURES_PROMPT",
    "OPPORTUNITIES_RISKS_PROMPT",
    # Monolithic baseline
    "MONOLITHIC_SPARC_PROMPT",
]
