"""
Player experience-focused SPARC agents.

Contains agents for evaluating player experience and theme aspects.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from sparc.llm.prompts.player_experience import (
    PLAYER_EXPERIENCE_PROMPT,
    THEME_PROMPT,
)
from sparc.llm.schemas.player_experience import (
    PlayerExperienceResponse,
    ThemeResponse,
)


class PlayerExperienceAgent(BaseAgent):
    """
    Agent for evaluating player experience.

    Analyzes the emotional experience players will have, checks for active
    voice, and creates high concept statements. Uses lower temperature for
    more analytical evaluation.
    """

    name = "player_experience"
    response_schema = PlayerExperienceResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for player experience evaluation."""
        game_text = data.get("game_text", "")
        return PLAYER_EXPERIENCE_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class ThemeAgent(BaseAgent):
    """
    Agent for evaluating thematic elements.

    Identifies dominant and secondary themes, evaluates consistency,
    and checks how well theme integrates across design aspects.
    """

    name = "theme"
    response_schema = ThemeResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for theme evaluation."""
        game_text = data.get("game_text", "")
        return THEME_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
