"""
Pillar operation handlers.

Each handler implements a specific pillar LLM operation.
Handlers are stateless and use the ModelManager for LLM interactions.
"""

from typing import Any, Dict

from llm_orchestrator.core import BaseOperationHandler, register_handler
from llm_orchestrator.exceptions import InvalidRequestError
from llm_orchestrator.operations.pillars.prompts import (
    ContextInPillarsPrompt,
    ImprovePillarPrompt,
    PillarAdditionPrompt,
    PillarCompletenessPrompt,
    PillarContradictionPrompt,
    ValidationPrompt,
)
from llm_orchestrator.operations.pillars.schemas import (
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
    response_schema = LLMPillar

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return ImprovePillarPrompt % (data["name"], data["description"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "name" not in data or "description" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )


class EvaluateCompletenessHandler(BaseOperationHandler):
    """Evaluate if pillars adequately cover the game design idea."""

    operation_id = "pillars.evaluate_completeness"
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


def register_all_handlers():
    """Register all pillar handlers with the global registry."""
    register_handler("pillars.validate", ValidatePillarHandler)
    register_handler("pillars.improve", ImprovePillarHandler)
    register_handler("pillars.evaluate_completeness", EvaluateCompletenessHandler)
    register_handler("pillars.evaluate_contradictions", EvaluateContradictionsHandler)
    register_handler("pillars.suggest_additions", SuggestAdditionsHandler)
    register_handler("pillars.evaluate_context", EvaluateContextHandler)


# Auto-register when module is imported
register_all_handlers()
