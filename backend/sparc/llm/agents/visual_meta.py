"""
Visual and meta SPARC agents.

Contains agents for evaluating unique features, art direction, and risks.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from sparc.llm.prompts.visual_meta import (
    ART_DIRECTION_PROMPT,
    OPPORTUNITIES_RISKS_PROMPT,
    UNIQUE_FEATURES_PROMPT,
)
from sparc.llm.schemas.visual_meta import (
    ArtDirectionResponse,
    OpportunitiesRisksResponse,
    UniqueFeaturesResponse,
)


class UniqueFeaturesAgent(BaseAgent):
    """
    Agent for evaluating unique features and differentiation.

    Analyzes uniqueness claims, validates them against existing games,
    and identifies defining elements. Uses slightly higher temperature
    to allow for creative comparison.
    """

    name = "unique_features"
    response_schema = UniqueFeaturesResponse
    temperature = 0.4  # Slightly higher for creative analysis

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for unique features evaluation."""
        game_text = data.get("game_text", "")
        return UNIQUE_FEATURES_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class ArtDirectionAgent(BaseAgent):
    """
    Agent for evaluating art direction and visual style.

    Analyzes art style, color palette, lighting, and visual uniqueness.
    Ensures art direction supports theme and gameplay.
    """

    name = "art_direction"
    response_schema = ArtDirectionResponse
    temperature = 0.4  # Slightly higher for creative visual analysis

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for art direction evaluation."""
        game_text = data.get("game_text", "")
        return ART_DIRECTION_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class OpportunitiesRisksAgent(BaseAgent):
    """
    Agent for evaluating opportunities and risks.

    Analyzes market opportunities, creative opportunities, and potential
    risks with mitigation strategies. Critical for project feasibility.
    """

    name = "opportunities_risks"
    response_schema = OpportunitiesRisksResponse
    temperature = 0.3  # Lower for analytical risk assessment

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for opportunities/risks evaluation."""
        game_text = data.get("game_text", "")
        return OPPORTUNITIES_RISKS_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
