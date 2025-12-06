"""
Node operation handlers.

Each handler implements a specific node LLM operation.
Handlers are stateless and use the ModelManager for LLM interactions.
"""

from typing import Any, Dict

from llm import BaseOperationHandler
from llm.exceptions import InvalidRequestError
from pxnodes.llm.prompts import (
    ImproveNodeWithExplanationPrompt,
    NodeValidationPrompt,
)
from pxnodes.llm.schemas import (
    ImprovedNodeResponse,
    NodeValidationResponse,
)


def format_components_text(components: list[Dict[str, Any]]) -> str:
    """Format components as text for prompts."""
    if not components:
        return "No components attached to this node."

    lines = []
    for comp in components:
        comp_id = comp.get("component_id", "unknown")
        definition_name = comp.get("definition_name", "Unknown")
        definition_type = comp.get("definition_type", "unknown")
        value = comp.get("value")
        value_str = str(value) if value is not None else "null"
        lines.append(
            f"- [ID: {comp_id}] {definition_name} ({definition_type}): {value_str}"
        )

    return "\n".join(lines)


class ValidateNodeHandler(BaseOperationHandler):
    """Validate a game design node for coherence issues."""

    operation_id = "nodes.validate"
    description = (
        "Validate a game design node for coherence between name, "
        "description, and components"
    )
    version = "1.0.0"
    response_schema = NodeValidationResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        components_text = format_components_text(data.get("components", []))
        return NodeValidationPrompt % (
            data["name"],
            data["description"],
            components_text,
        )

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "name" not in data or "description" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )


class ImproveNodeWithExplanationHandler(BaseOperationHandler):
    """Improve a node and explain the improvements made."""

    operation_id = "nodes.improve_explained"
    description = "Generate improved node with detailed explanations of changes"
    version = "1.0.0"
    response_schema = ImprovedNodeResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        # Format validation issues for the prompt
        issues = data.get("validation_issues", [])
        if issues:
            issues_text = "\n".join(
                [
                    f"{i+1}. {issue.get('title', 'Unknown')}: "
                    f"{issue.get('description', '')}"
                    for i, issue in enumerate(issues)
                ]
            )
            issues_text = f"Total issues to fix: {len(issues)}\n\n{issues_text}"
        else:
            issues_text = (
                "No specific issues provided. Improve for clarity and coherence."
            )

        components_text = format_components_text(data.get("components", []))

        return ImproveNodeWithExplanationPrompt % (
            issues_text,
            data["name"],
            data["description"],
            components_text,
        )

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "name" not in data or "description" not in data:
            raise InvalidRequestError(
                message="Missing required fields: 'name' and 'description'"
            )
