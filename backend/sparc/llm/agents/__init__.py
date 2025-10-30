"""
SPARC agents for agentic evaluation.

Re-exports all SPARC agents for easy importing.
"""

# Gameplay agents
from sparc.llm.agents.gameplay import GameplayAgent, GoalsChallengesRewardsAgent

# Player experience agents
from sparc.llm.agents.player_experience import (
    PlayerExperienceAgent,
    PurposeAgent,
    ThemeAgent,
)

# Visual and meta agents
from sparc.llm.agents.visual_meta import (
    ArtDirectionAgent,
    OpportunitiesRisksAgent,
    UniqueFeaturesAgent,
)

# World building agents
from sparc.llm.agents.world import PlaceAgent, StoryNarrativeAgent

__all__ = [
    # Player-focused (3 agents)
    "PlayerExperienceAgent",
    "ThemeAgent",
    "PurposeAgent",
    # Gameplay (2 agents)
    "GameplayAgent",
    "GoalsChallengesRewardsAgent",
    # World building (2 agents)
    "PlaceAgent",
    "StoryNarrativeAgent",
    # Visual and meta (3 agents)
    "UniqueFeaturesAgent",
    "ArtDirectionAgent",
    "OpportunitiesRisksAgent",
]
