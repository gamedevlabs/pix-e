"""
SPARC V2 aspect evaluation agents.

Contains all 10 specialized V2 agents for router-based agentic evaluation.
"""

from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.prompts.v2.art_direction import ART_DIRECTION_PROMPT
from sparc.llm.prompts.v2.gameplay import GAMEPLAY_PROMPT
from sparc.llm.prompts.v2.goals_challenges import GOALS_CHALLENGES_REWARDS_PROMPT
from sparc.llm.prompts.v2.opportunities_risks import OPPORTUNITIES_RISKS_PROMPT
from sparc.llm.prompts.v2.place import PLACE_PROMPT
from sparc.llm.prompts.v2.player_experience import PLAYER_EXPERIENCE_PROMPT
from sparc.llm.prompts.v2.purpose import PURPOSE_PROMPT
from sparc.llm.prompts.v2.story_narrative import STORY_NARRATIVE_PROMPT
from sparc.llm.prompts.v2.theme import THEME_PROMPT
from sparc.llm.prompts.v2.unique_features import UNIQUE_FEATURES_PROMPT

# =============================================================================
# Player Experience Agents (3)
# =============================================================================


class PlayerExperienceAgentV2(AspectAgentV2):
    """Evaluates player experience definition."""

    name = "player_experience_v2"
    aspect_name = "player_experience"
    prompt_template = PLAYER_EXPERIENCE_PROMPT
    default_suggestions = [
        "Describe the player experience from the player's perspective "
        "using active form.",
        "Focus on emotional keywords: what should players FEEL?",
        "Create a 1-2 sentence high concept statement.",
    ]


class ThemeAgentV2(AspectAgentV2):
    """Evaluates theme definition."""

    name = "theme_v2"
    aspect_name = "theme"
    prompt_template = THEME_PROMPT
    default_suggestions = [
        "Define the dominant, unifying theme of your game.",
        "Identify secondary themes that complement the main theme.",
        "Consider how themes connect to gameplay and narrative.",
    ]


class PurposeAgentV2(AspectAgentV2):
    """Evaluates purpose definition."""

    name = "purpose_v2"
    aspect_name = "purpose"
    prompt_template = PURPOSE_PROMPT
    default_suggestions = [
        "State the purpose of this project clearly.",
        "Explain why YOU want to work on this project.",
        "Define what you want to achieve by completing this project.",
    ]


# =============================================================================
# Gameplay Agents (2)
# =============================================================================


class GameplayAgentV2(AspectAgentV2):
    """Evaluates gameplay definition."""

    name = "gameplay_v2"
    aspect_name = "gameplay"
    prompt_template = GAMEPLAY_PROMPT
    default_suggestions = [
        "List 3-5 core verbs that describe player actions.",
        "Describe the core mechanics players interact with.",
        "Define the 30-second gameplay loop.",
    ]


class GoalsChallengesRewardsAgentV2(AspectAgentV2):
    """Evaluates goals, challenges, and rewards definition."""

    name = "goals_challenges_rewards_v2"
    aspect_name = "goals_challenges_rewards"
    prompt_template = GOALS_CHALLENGES_REWARDS_PROMPT
    default_suggestions = [
        "List the objectives players must complete.",
        "Define obstacles and challenges for each objective.",
        "Describe rewards for completing objectives.",
        "Plan how to communicate objectives to players.",
    ]


# =============================================================================
# World Building Agents (2)
# =============================================================================


class PlaceAgentV2(AspectAgentV2):
    """Evaluates place/setting definition."""

    name = "place_v2"
    aspect_name = "place"
    prompt_template = PLACE_PROMPT
    default_suggestions = [
        "Define the environment setting and world type.",
        "List concrete key locations with specific names.",
        "Describe the atmosphere and feel of each location.",
    ]


class StoryNarrativeAgentV2(AspectAgentV2):
    """Evaluates story and narrative definition."""

    name = "story_narrative_v2"
    aspect_name = "story_narrative"
    prompt_template = STORY_NARRATIVE_PROMPT
    default_suggestions = [
        "Describe the story of the game or level.",
        "Explain what happened before the player arrived.",
        "Define how and why the player arrives at this place.",
        "Plan storytelling methods (environmental, dialogue, etc.).",
    ]


# =============================================================================
# Visual and Meta Agents (3)
# =============================================================================


class UniqueFeaturesAgentV2(AspectAgentV2):
    """Evaluates unique features definition."""

    name = "unique_features_v2"
    aspect_name = "unique_features"
    prompt_template = UNIQUE_FEATURES_PROMPT
    temperature = 0.4  # Slightly more creative
    default_suggestions = [
        "Identify what makes your game unique.",
        "Explain how it differs from similar games.",
        "List 3-5 defining elements that set it apart.",
    ]


class ArtDirectionAgentV2(AspectAgentV2):
    """Evaluates art direction definition."""

    name = "art_direction_v2"
    aspect_name = "art_direction"
    prompt_template = ART_DIRECTION_PROMPT
    temperature = 0.4  # Slightly more creative
    default_suggestions = [
        "Specify the art style (realistic, stylized, cartoonish, etc.).",
        "Define the color palette (primary, secondary, light/shadow).",
        "Describe lighting and atmosphere.",
        "Gather visual references and create a mood board.",
    ]


class OpportunitiesRisksAgentV2(AspectAgentV2):
    """Evaluates opportunities and risks definition."""

    name = "opportunities_risks_v2"
    aspect_name = "opportunities_risks"
    prompt_template = OPPORTUNITIES_RISKS_PROMPT
    default_suggestions = [
        "List opportunities and how to leverage them.",
        "Identify potential risks and their likelihood.",
        "Describe mitigation strategies for each risk.",
    ]
