"""
Pillar evaluation agents for agentic execution mode.

Each agent implements a specialized evaluation task that can run in parallel
with other agents as part of an agent workflow.
"""

from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from llm.exceptions import InvalidRequestError
from pillars.llm.prompts import (
    ConceptFitPrompt,
    ContradictionResolutionPrompt,
    PillarAdditionPrompt,
    PillarAdditionPromptSimple,
    PillarContradictionPrompt,
)
from pillars.llm.schemas import (
    ContradictionResolutionResponse,
    PillarAdditionsFeedback,
    PillarCompletenessResponse,
    PillarContradictionResponse,
)


class ConceptFitAgent(BaseAgent):
    """
    Agent for evaluating pillar concept fit.

    Analyzes whether the provided pillars adequately fit the game concept
    and identifies any gaps in coverage.
    """

    name = "concept_fit"
    response_schema = PillarCompletenessResponse
    temperature = 0.3

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for concept fit evaluation."""
        pillars_text = data["pillars_text"]
        context = data["context"]
        return ConceptFitPrompt % (context, pillars_text)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


# Alias for backwards compatibility
EvaluateCompletenessAgent = ConceptFitAgent


class ContradictionsAgent(BaseAgent):
    """
    Agent for evaluating pillar contradictions.

    Identifies contradictions and conflicts between design pillars
    that could lead to inconsistent game design.
    """

    name = "contradictions"
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


# Alias for backwards compatibility
EvaluateContradictionsAgent = ContradictionsAgent


class SuggestAdditionsAgent(BaseAgent):
    """
    Agent for suggesting additional pillars.

    Suggests new pillars that could better cover missing aspects
    of the game design. Can be enriched with concept fit feedback
    for more targeted suggestions.
    """

    name = "suggest_additions"
    response_schema = PillarAdditionsFeedback
    temperature = 0.4

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for suggesting additional pillars.

        If concept_fit_feedback is provided, uses enhanced prompt with that context.
        Otherwise, uses simple prompt for standalone use.
        """
        pillars_text = data["pillars_text"]
        context = data["context"]
        concept_fit_feedback = data.get("concept_fit_feedback")

        if concept_fit_feedback:
            # Format concept fit feedback into readable text
            feedback_text = self._format_concept_fit_feedback(concept_fit_feedback)
            return PillarAdditionPrompt % (context, pillars_text, feedback_text)
        else:
            # Use simple prompt without concept fit context
            return PillarAdditionPromptSimple % (context, pillars_text)

    def _format_concept_fit_feedback(self, feedback: Dict[str, Any]) -> str:
        """Format concept fit feedback into readable text for the prompt."""
        lines = []

        # Add missing aspects if available
        missing_aspects = feedback.get("missingAspects", [])
        if missing_aspects:
            lines.append("Missing aspects that need pillar coverage:")
            for aspect in missing_aspects:
                lines.append(f"  - {aspect}")
            lines.append("")

        # Add pillar feedback summary if available
        pillar_feedback = feedback.get("pillarFeedback", [])
        if pillar_feedback:
            lines.append("Current pillar analysis:")
            for pf in pillar_feedback:
                name = pf.get("name", "Unknown")
                reasoning = pf.get("reasoning", "")
                lines.append(f"  - {name}: {reasoning}")

        return "\n".join(lines) if lines else "No specific gaps identified."

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )


class ContradictionResolutionAgent(BaseAgent):
    """
    Agent for suggesting contradiction resolutions.

    Takes contradiction detection results and suggests ways to resolve
    the identified conflicts between pillars.
    """

    name = "contradiction_resolution"
    response_schema = ContradictionResolutionResponse
    temperature = 0.4

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for contradiction resolution suggestions."""
        pillars_text = data["pillars_text"]
        context = data["context"]
        contradictions_feedback = data.get("contradictions_feedback")

        if not contradictions_feedback:
            raise InvalidRequestError(
                message="ContradictionResolutionAgent requires "
                "'contradictions_feedback'"
            )

        # Format contradictions into readable text
        contradictions_text = self._format_contradictions(contradictions_feedback)
        return ContradictionResolutionPrompt % (
            context,
            pillars_text,
            contradictions_text,
        )

    def _format_contradictions(self, feedback: Dict[str, Any]) -> str:
        """Format contradictions feedback into readable text for the prompt."""
        contradictions = feedback.get("contradictions", [])
        if not contradictions:
            return "No contradictions provided."

        lines = []
        for i, c in enumerate(contradictions, 1):
            pillar_one = c.get("pillarOneTitle", "Pillar 1")
            pillar_two = c.get("pillarTwoTitle", "Pillar 2")
            reason = c.get("reason", "No reason provided")
            lines.append(f"{i}. {pillar_one} vs {pillar_two}:")
            lines.append(f"   Conflict: {reason}")
            lines.append("")

        return "\n".join(lines)

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data has required fields."""
        if "pillars_text" not in data or "context" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'pillars_text' and 'context'"
            )
        if "contradictions_feedback" not in data:
            raise InvalidRequestError(
                message="Missing required field: 'contradictions_feedback'"
            )
