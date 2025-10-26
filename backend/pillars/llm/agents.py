"""
Pillar evaluation agents for agentic execution mode.

Each agent implements a specialized evaluation task that can run in parallel
with other agents as part of an agent graph.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from pillars.llm.prompts import (
    PillarAdditionPrompt,
    PillarCompletenessPrompt,
    PillarContradictionPrompt,
)
from pillars.llm.schemas import (
    PillarAdditionsFeedback,
    PillarCompletenessResponse,
    PillarContradictionResponse,
)


class EvaluateCompletenessAgent(BaseAgent):
    """
    Agent for evaluating pillar completeness.

    Analyzes whether the provided pillars adequately cover all aspects
    of the game design based on the given context.
    """

    name = "evaluate_completeness"
    response_schema = PillarCompletenessResponse
    temperature = 0.3

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for completeness evaluation."""
        pillars_text = data["pillars_text"]
        context = data["context"]
        return PillarCompletenessPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class EvaluateContradictionsAgent(BaseAgent):
    """
    Agent for evaluating pillar contradictions.

    Identifies contradictions and conflicts between design pillars
    that could lead to inconsistent game design.
    """

    name = "evaluate_contradictions"
    response_schema = PillarContradictionResponse
    temperature = 0.3

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for contradiction detection."""
        pillars_text = data["pillars_text"]
        context = data["context"]
        return PillarContradictionPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class SuggestAdditionsAgent(BaseAgent):
    """
    Agent for suggesting additional pillars.

    Suggests new pillars that could better cover missing aspects
    of the game design based on context analysis.
    """

    name = "suggest_additions"
    response_schema = PillarAdditionsFeedback
    temperature = 0.4

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for suggesting additional pillars."""
        pillars_text = data["pillars_text"]
        context = data["context"]
        return PillarAdditionPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )
