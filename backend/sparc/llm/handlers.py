"""
SPARC operation handlers.

Contains handlers for both monolithic (baseline) and agentic SPARC evaluations.
"""

from typing import Any, Dict

from llm.exceptions import InvalidRequestError
from llm.operation_handler import BaseOperationHandler
from sparc.llm.prompts.monolithic import MONOLITHIC_SPARC_PROMPT
from sparc.llm.schemas.aggregated import MonolithicSPARCResponse


class MonolithicSPARCHandler(BaseOperationHandler):
    """
    Monolithic SPARC handler (baseline for comparison).

    Uses the original single-shot prompt to evaluate all SPARC aspects
    in one LLM call. This serves as the baseline to compare against
    the agentic multi-agent approach.

    Temperature: 0
    """

    operation_id = "sparc.monolithic"
    response_schema = MonolithicSPARCResponse
    temperature = 0

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build monolithic SPARC evaluation prompt.

        Args:
            data: Must contain 'game_text' key with game description

        Returns:
            Formatted prompt string
        """
        game_text = data.get("game_text", "")
        return MONOLITHIC_SPARC_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate that required input fields are present.

        Args:
            data: Input data dictionary

        Raises:
            InvalidRequestError: If game_text is missing or empty
        """
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
