"""
Gameplay-focused SPARC agents.

Contains agents for evaluating gameplay mechanics.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from sparc.llm.prompts.gameplay import GAMEPLAY_PROMPT
from sparc.llm.schemas.gameplay import GameplayResponse


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
