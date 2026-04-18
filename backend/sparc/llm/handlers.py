"""
SPARC operation handlers.

Contains handlers for both monolithic (baseline) and agentic SPARC evaluations.
"""

import json
from typing import Any, Dict

from llm.exceptions import InvalidRequestError
from llm.operation_handler import BaseOperationHandler
from sparc.llm.prompts.monolithic import MONOLITHIC_SPARC_PROMPT
from sparc.llm.prompts.monolithic_rq1 import MONOLITHIC_RQ1_PROMPT
from sparc.llm.prompts.monolithic_synthesis import (
    MONOLITHIC_SPARC_SYNTHESIS_PROMPT,
)
from sparc.llm.prompts.rq1_normalize import RQ1_NORMALIZE_PROMPT
from sparc.llm.schemas.aggregated import MonolithicSPARCResponse
from sparc.llm.schemas.rq1 import RQ1UnifiedResponse
from sparc.llm.schemas.v2.synthesis import SPARCSynthesis


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


class MonolithicSPARCSynthesisHandler(BaseOperationHandler):
    """
    Monolithic SPARC synthesis handler (RQ1 summary baseline).

    Returns the same synthesis schema as the agentic workflow for
    apples-to-apples evaluation.
    """

    operation_id = "sparc.monolithic_synthesis"
    response_schema = SPARCSynthesis
    temperature = 0

    def build_prompt(self, data: Dict[str, Any]) -> str:
        game_text = data.get("game_text", "")
        return MONOLITHIC_SPARC_SYNTHESIS_PROMPT % game_text

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )


class RQ1NormalizeHandler(BaseOperationHandler):
    """
    Normalize SPARC evaluation output into the RQ1 synthesis schema.
    """

    operation_id = "sparc.rq1_normalize"
    response_schema = SPARCSynthesis
    temperature = 0

    def build_prompt(self, data: Dict[str, Any]) -> str:
        evaluation_output = data.get("evaluation_output", {})
        evaluation_type = data.get("evaluation_type", "unknown")
        evaluation_json = json.dumps(evaluation_output, indent=2, ensure_ascii=True)
        return RQ1_NORMALIZE_PROMPT % (evaluation_type, evaluation_json)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "evaluation_output" not in data or not data["evaluation_output"]:
            raise InvalidRequestError(
                message="Missing required field: 'evaluation_output'",
                context={"received_keys": list(data.keys())},
            )


class MonolithicRQ1Handler(BaseOperationHandler):
    """
    Monolithic handler for RQ1 experiment.

    Produces per-aspect structured output AND synthesis in a single LLM call,
    using the same output schema as the agentic pipeline.
    Eliminates the need for post-hoc normalization.
    """

    operation_id = "sparc.monolithic_rq1"
    response_schema = RQ1UnifiedResponse
    temperature = 0

    def build_prompt(self, data: Dict[str, Any]) -> str:
        game_text = data.get("game_text", "")
        return MONOLITHIC_RQ1_PROMPT.format(game_text=game_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "game_text" not in data or not data["game_text"]:
            raise InvalidRequestError(
                message="Missing required field: 'game_text'",
                context={"received_keys": list(data.keys())},
            )
