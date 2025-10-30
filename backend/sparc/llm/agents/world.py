"""
World-building SPARC agents.

Contains agents for evaluating place/environment and story/narrative aspects.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from sparc.llm.prompts.world import PLACE_PROMPT, STORY_NARRATIVE_PROMPT
from sparc.llm.schemas.world import PlaceResponse, StoryNarrativeResponse


class PlaceAgent(BaseAgent):
    """
    Agent for evaluating place and environment.

    Analyzes environment settings, key locations, and location specificity.
    Checks if locations are concrete enough for level design.
    """

    name = "place"
    response_schema = PlaceResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for place evaluation."""
        game_text = data.get("game_text", "")
        return PLACE_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class StoryNarrativeAgent(BaseAgent):
    """
    Agent for evaluating story and narrative structure.

    Analyzes story summary, storytelling methods, player arrival context,
    key events, and navigation flow. Ensures interactive narrative coherence.
    """

    name = "story_narrative"
    response_schema = StoryNarrativeResponse
    temperature = 0.3  # Lower for analytical evaluation

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for story/narrative evaluation."""
        game_text = data.get("game_text", "")
        return STORY_NARRATIVE_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
