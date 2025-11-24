"""
SPARC V2 agents.

Router-based agentic evaluation with simplified output format.
"""

from sparc.llm.agents.v2.art_direction import ArtDirectionAgentV2
from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.agents.v2.gameplay import GameplayAgentV2
from sparc.llm.agents.v2.goals_challenges import GoalsChallengesRewardsAgentV2
from sparc.llm.agents.v2.opportunities_risks import OpportunitiesRisksAgentV2
from sparc.llm.agents.v2.place import PlaceAgentV2
from sparc.llm.agents.v2.player_experience import PlayerExperienceAgentV2
from sparc.llm.agents.v2.purpose import PurposeAgentV2
from sparc.llm.agents.v2.router import RouterAgent
from sparc.llm.agents.v2.story_narrative import StoryNarrativeAgentV2
from sparc.llm.agents.v2.synthesis import SynthesisAgent
from sparc.llm.agents.v2.theme import ThemeAgentV2
from sparc.llm.agents.v2.unique_features import UniqueFeaturesAgentV2

__all__ = [
    # Base classes
    "V2BaseAgent",
    "AspectAgentV2",
    # Router
    "RouterAgent",
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
