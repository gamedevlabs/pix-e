"""
SPARC aspect evaluation agents.

Contains all 10 specialized agents for evaluating game concepts across
the SPARC framework dimensions.
"""

from sparc.llm.agents.base import SPARCBaseAgent
from sparc.llm.prompts.gameplay import (
    GAMEPLAY_PROMPT,
    GOALS_CHALLENGES_REWARDS_PROMPT,
)
from sparc.llm.prompts.player_experience import (
    PLAYER_EXPERIENCE_PROMPT,
    PURPOSE_PROMPT,
    THEME_PROMPT,
)
from sparc.llm.prompts.visual_meta import (
    ART_DIRECTION_PROMPT,
    OPPORTUNITIES_RISKS_PROMPT,
    UNIQUE_FEATURES_PROMPT,
)
from sparc.llm.prompts.world import PLACE_PROMPT, STORY_NARRATIVE_PROMPT
from sparc.llm.schemas.gameplay import (
    GameplayResponse,
    GoalsChallengesRewardsResponse,
)
from sparc.llm.schemas.player_experience import (
    PlayerExperienceResponse,
    PurposeResponse,
    ThemeResponse,
)
from sparc.llm.schemas.visual_meta import (
    ArtDirectionResponse,
    OpportunitiesRisksResponse,
    UniqueFeaturesResponse,
)
from sparc.llm.schemas.world import PlaceResponse, StoryNarrativeResponse

# =============================================================================
# Player Experience Agents (3)
# =============================================================================


class PlayerExperienceAgent(SPARCBaseAgent):
    """Evaluates emotional player experience and high concept statements."""

    name = "player_experience"
    response_schema = PlayerExperienceResponse
    temperature = 0
    prompt_template = PLAYER_EXPERIENCE_PROMPT


class ThemeAgent(SPARCBaseAgent):
    """Evaluates thematic elements and consistency across design aspects."""

    name = "theme"
    response_schema = ThemeResponse
    temperature = 0
    prompt_template = THEME_PROMPT


class PurposeAgent(SPARCBaseAgent):
    """Evaluates project purpose, creator motivation, and sustainability."""

    name = "purpose"
    response_schema = PurposeResponse
    temperature = 0
    prompt_template = PURPOSE_PROMPT


# =============================================================================
# Gameplay Agents (2)
# =============================================================================


class GameplayAgent(SPARCBaseAgent):
    """Evaluates core mechanics, verbs, and 30-second gameplay loops."""

    name = "gameplay"
    response_schema = GameplayResponse
    temperature = 0
    prompt_template = GAMEPLAY_PROMPT


class GoalsChallengesRewardsAgent(SPARCBaseAgent):
    """Evaluates objectives, obstacles, and reward systems."""

    name = "goals_challenges_rewards"
    response_schema = GoalsChallengesRewardsResponse
    temperature = 0
    prompt_template = GOALS_CHALLENGES_REWARDS_PROMPT


# =============================================================================
# World Building Agents (2)
# =============================================================================


class PlaceAgent(SPARCBaseAgent):
    """Evaluates environment settings and location specificity."""

    name = "place"
    response_schema = PlaceResponse
    temperature = 0
    prompt_template = PLACE_PROMPT


class StoryNarrativeAgent(SPARCBaseAgent):
    """Evaluates story structure, storytelling methods, and narrative flow."""

    name = "story_narrative"
    response_schema = StoryNarrativeResponse
    temperature = 0
    prompt_template = STORY_NARRATIVE_PROMPT


# =============================================================================
# Visual and Meta Agents (3)
# =============================================================================


class UniqueFeaturesAgent(SPARCBaseAgent):
    """Evaluates uniqueness claims and differentiating elements."""

    name = "unique_features"
    response_schema = UniqueFeaturesResponse
    temperature = 0
    prompt_template = UNIQUE_FEATURES_PROMPT


class ArtDirectionAgent(SPARCBaseAgent):
    """Evaluates art style, color palette, and visual uniqueness."""

    name = "art_direction"
    response_schema = ArtDirectionResponse
    temperature = 0
    prompt_template = ART_DIRECTION_PROMPT


class OpportunitiesRisksAgent(SPARCBaseAgent):
    """Evaluates market opportunities and risks with mitigation strategies."""

    name = "opportunities_risks"
    response_schema = OpportunitiesRisksResponse
    temperature = 0
    prompt_template = OPPORTUNITIES_RISKS_PROMPT
