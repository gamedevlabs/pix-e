"""
SPARC agents for agentic evaluation.

Re-exports all 10 SPARC aspect agents.
"""

from sparc.llm.agents.aspects import (
    ArtDirectionAgent,
    GameplayAgent,
    GoalsChallengesRewardsAgent,
    OpportunitiesRisksAgent,
    PlaceAgent,
    PlayerExperienceAgent,
    PurposeAgent,
    StoryNarrativeAgent,
    ThemeAgent,
    UniqueFeaturesAgent,
)

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
