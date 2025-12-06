"""
Response schemas for node validation operations.

These Pydantic models define the structure of LLM responses.
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class CoherenceIssue(BaseModel):
    """A coherence issue found during node validation."""

    title: str = Field(description="Short title of the issue")
    description: str = Field(description="Detailed description of what's wrong")
    severity: int = Field(
        ge=1, le=5, description="Severity of the issue, from 1 (low) to 5 (high)"
    )
    issue_type: Literal[
        "title_description_mismatch",
        "component_value_contradiction",
        "component_irrelevance",
        "unclear_purpose",
        "component_conflict",
    ] = Field(description="Category of the issue")
    related_components: list[str] = Field(
        default_factory=list, description="Names of components involved in this issue"
    )


class NodeValidationResponse(BaseModel):
    """Response for node validation operation."""

    has_issues: bool = Field(description="Whether any coherence issues were found")
    issues: list[CoherenceIssue] = Field(
        default_factory=list, description="List of coherence issues found"
    )
    overall_coherence_score: int = Field(
        ge=1,
        le=10,
        description=(
            "Overall coherence score from 1 (incoherent) to 10 (perfectly coherent)"
        ),
    )
    summary: str = Field(description="Brief summary of the node's coherence state")


class NodeChange(BaseModel):
    """Describes a specific change made to improve a node."""

    field: Literal["name", "description"] = Field(description="Which field was changed")
    after: str = Field(description="The new value after improvement")
    reasoning: str = Field(description="Why this change improves the node")
    issues_addressed: list[str] = Field(
        default_factory=list,
        description="Which validation issues this change fixes (can be empty list)",
    )


class ComponentChange(BaseModel):
    """A suggested change for a component value."""

    component_id: str = Field(description="UUID of the component to change")
    component_name: str = Field(description="Name of the component definition")
    current_value: Optional[Union[str, int, float, bool]] = Field(
        default=None, description="Current value of the component"
    )
    suggested_value: Optional[Union[str, int, float, bool]] = Field(
        default=None, description="Suggested new value"
    )
    reasoning: str = Field(description="Why this value change would improve coherence")
    issues_addressed: list[str] = Field(
        default_factory=list,
        description="Which validation issues this change fixes",
    )


class ImprovedNodeResponse(BaseModel):
    """Response containing improved node with explanations."""

    name: str = Field(description="Improved node name")
    description: str = Field(description="Improved node description")
    changes: list[NodeChange] = Field(
        default_factory=list,
        description="List of text field changes made with explanations",
    )
    component_changes: list[ComponentChange] = Field(
        default_factory=list,
        description="List of component value changes with explanations",
    )
    overall_summary: str = Field(
        description="High-level summary of why the improved node is better"
    )
    validation_issues_fixed: list[str] = Field(
        default_factory=list,
        description="List of validation issue titles that were fixed",
    )
