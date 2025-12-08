"""
Base classes for SPARC V1 agents.

Provides shared validation and utilities for all SPARC agents.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError


class SPARCBaseAgent(BaseAgent):
    """
    Base class for SPARC V1 agents with shared validation.

    Subclasses must define:
        - name: Agent identifier
        - response_schema: Pydantic model for response validation
        - prompt_template: String template with %s placeholder for game_text
    """

    prompt_template: str = ""  # Subclasses must override

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt by substituting game_text into the template."""
        game_text = data.get("game_text", "")
        return self.prompt_template % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data has required field 'game_text'.
        """
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
