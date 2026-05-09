"""
SPARC V2 agents.

Router-based agentic evaluation with simplified output format.
"""

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.agents.v2.aspects import (
    ArtDirectionAgentV2,
    GameplayAgentV2,
    GoalsChallengesRewardsAgentV2,
    OpportunitiesRisksAgentV2,
    PlaceAgentV2,
    PlayerExperienceAgentV2,
    PurposeAgentV2,
    StoryNarrativeAgentV2,
    ThemeAgentV2,
    UniqueFeaturesAgentV2,
)
from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.agents.v2.pillar_context import PillarContextAgent
from sparc.llm.agents.v2.router import RouterAgent
from sparc.llm.agents.v2.synthesis import SynthesisAgent

__all__ = [
    # Base classes
    "V2BaseAgent",
    "AspectAgentV2",
    # Router
    "RouterAgent",
    # Pillar context
    "PillarContextAgent",
    # Aspect agents
    "PlayerExperienceAgentV2",
    "ThemeAgentV2",
    "PurposeAgentV2",
    "GameplayAgentV2",
    "GoalsChallengesRewardsAgentV2",
    "PlaceAgentV2",
    "StoryNarrativeAgentV2",
    "UniqueFeaturesAgentV2",
    "ArtDirectionAgentV2",
    "OpportunitiesRisksAgentV2",
    # Synthesis
    "SynthesisAgent",
]
