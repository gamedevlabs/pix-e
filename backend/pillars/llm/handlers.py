"""
Pillar operation handlers.

Each handler implements a specific pillar LLM operation.
Handlers are stateless and use the ModelManager for LLM interactions.
"""

from typing import Any, Dict

from llm import BaseOperationHandler
from llm.exceptions import InvalidRequestError
from pillars.llm.prompts import (
    ContextInPillarsPrompt,
    ImprovePillarPrompt,
    PillarAdditionPrompt,
    PillarCompletenessPrompt,
    PillarContradictionPrompt,
    ValidationPrompt,
)
from pillars.llm.schemas import (
    ContextInPillarsResponse,
    LLMPillar,
    PillarAdditionsFeedback,
    PillarCompletenessResponse,
    PillarContradictionResponse,
    PillarResponse,
)


class ValidatePillarHandler(BaseOperationHandler):
    """Validate a game design pillar for structural issues."""

    operation_id = "pillars.validate"
    description = "Validate a game design pillar for structural issues and clarity"
    version = "1.0.0"
    response_schema = PillarResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return ValidationPrompt % (data["name"], data["description"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "name" not in data or "description" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )


class ImprovePillarHandler(BaseOperationHandler):
    """Improve a game design pillar by fixing structural issues."""

    operation_id = "pillars.improve"
    description = "Generate an improved version of a pillar by fixing structural issues"
    version = "1.0.0"
    response_schema = LLMPillar

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return ImprovePillarPrompt % (data["name"], data["description"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "name" not in data or "description" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )


class EvaluateCompletenessHandler(BaseOperationHandler):
    """Evaluate if pillars adequately cover the game design."""

    operation_id = "pillars.evaluate_completeness"
    description = "Check if pillars adequately cover all aspects of the game design"
    version = "1.0.0"
    response_schema = PillarCompletenessResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        pillars_text = data["pillars_text"]  # Pre-formatted from view
        context = data["context"]
        return PillarCompletenessPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class EvaluateContradictionsHandler(BaseOperationHandler):
    """Evaluate if pillars contradict each other."""

    operation_id = "pillars.evaluate_contradictions"
    description = "Find contradictions and conflicts between design pillars"
    version = "1.0.0"
    response_schema = PillarContradictionResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        pillars_text = data["pillars_text"]
        context = data["context"]
        return PillarContradictionPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class SuggestAdditionsHandler(BaseOperationHandler):
    """Suggest additional pillars to better cover the game design."""

    operation_id = "pillars.suggest_additions"
    description = "Suggest additional pillars to cover missing aspects of the design"
    version = "1.0.0"
    response_schema = PillarAdditionsFeedback

    def build_prompt(self, data: Dict[str, Any]) -> str:
        pillars_text = data["pillars_text"]
        context = data["context"]
        return PillarAdditionPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class EvaluateContextHandler(BaseOperationHandler):
    """Evaluate how well a context/idea aligns with pillars."""

    operation_id = "pillars.evaluate_context"
    description = "Evaluate how well a game concept or idea aligns with design pillars"
    version = "1.0.0"
    response_schema = ContextInPillarsResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        pillars_text = data["pillars_text"]
        context = data["context"]
        return ContextInPillarsPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


# Handlers auto-register via BaseOperationHandler.__init_subclass__ on import
