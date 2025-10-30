"""
Gameplay-focused SPARC agents.

Contains agents for evaluating gameplay mechanics and goals/challenges/rewards.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from sparc.llm.prompts.gameplay import (
    GAMEPLAY_PROMPT,
    GOALS_CHALLENGES_REWARDS_PROMPT,
)
from sparc.llm.schemas.gameplay import (
    GameplayResponse,
    GoalsChallengesRewardsResponse,
)


class GameplayAgent(BaseAgent):
    """
    Agent for evaluating gameplay mechanics.

    Analyzes core verbs, mechanics clarity, and 30-second gameplay loops.
    Checks if gameplay is well-defined enough for development.
    """

    name = "gameplay"
    response_schema = GameplayResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for gameplay evaluation."""
        game_text = data.get("game_text", "")
        return GAMEPLAY_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class GoalsChallengesRewardsAgent(BaseAgent):
    """
    Agent for evaluating goals, challenges, and rewards structure.

    Analyzes objectives, obstacles, reward systems, and their integration
    with story. Ensures player motivation is properly designed.
    """

    name = "goals_challenges_rewards"
    response_schema = GoalsChallengesRewardsResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for goals/challenges/rewards evaluation."""
        game_text = data.get("game_text", "")
        return GOALS_CHALLENGES_REWARDS_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
