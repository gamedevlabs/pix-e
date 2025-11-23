"""
Response schemas for pillar operations.

These Pydantic models define the structure of LLM responses.
All schemas are migrated from backend/llm/llm_links/responseSchemes.py to centralize
pillar-specific logic in the orchestrator.
"""

from typing import Literal

from pydantic import BaseModel, Field


class StructuralIssue(BaseModel):
    title: str
    description: str
    severity: int = Field(
        ge=1, le=5, description="Severity of the issue, from 1 (low) to 5 (high)"
    )


class PillarResponse(BaseModel):
    hasStructureIssue: bool
    structuralIssues: list[StructuralIssue]
    content_feedback: str


class LLMPillar(BaseModel):
    pillarId: int
    name: str
    description: str


class CompletenessAnswer(BaseModel):
    pillarId: int  # Security Risk, letting AI inject IDs
    name: str
    reasoning: str


class ContradictionIssue(BaseModel):
    pillarOneId: int
    pillarTwoId: int
    pillarOneTitle: str
    pillarTwoTitle: str
    reason: str


class PillarCompletenessResponse(BaseModel):
    """Response for concept fit evaluation."""

    hasGaps: bool = Field(
        description="Whether there are gaps in pillar coverage for the game concept"
    )
    pillarFeedback: list[CompletenessAnswer] = Field(
        description="Reasoning for each pillar's fit with the concept"
    )
    missingAspects: list[str] = Field(
        description="List of aspects from the game concept not covered by pillars. "
        "Empty list if no gaps."
    )


class PillarContradictionResponse(BaseModel):
    hasContradictions: bool
    contradictions: list[ContradictionIssue]


class PillarAdditionsFeedback(BaseModel):
    """Response for suggesting additional pillars."""

    additions: list[LLMPillar]  # ignore given pillarId, needs to be created by DB


class ResolutionSuggestion(BaseModel):
    """A suggestion for resolving a contradiction between two pillars."""

    pillarOneId: int = Field(description="ID of the first pillar in the contradiction")
    pillarTwoId: int = Field(description="ID of the second pillar in the contradiction")
    pillarOneTitle: str = Field(description="Title of the first pillar")
    pillarTwoTitle: str = Field(description="Title of the second pillar")
    resolutionStrategy: str = Field(
        description="Suggested approach to resolve the contradiction"
    )
    suggestedChanges: list[str] = Field(
        description="Specific changes to make to resolve the contradiction"
    )
    alternativeApproach: str = Field(
        default="",
        description="Alternative approach if the primary strategy doesn't work",
    )


class ContradictionResolutionResponse(BaseModel):
    """Response for contradiction resolution suggestions."""

    resolutions: list[ResolutionSuggestion] = Field(
        description="List of resolution suggestions for each contradiction"
    )
    overallRecommendation: str = Field(
        description="Overall recommendation for handling the contradictions"
    )


class PillarsInContextResponse(BaseModel):
    coverage: PillarCompletenessResponse
    contradictions: PillarContradictionResponse
    proposedAdditions: PillarAdditionsFeedback


class ContextInPillarsResponse(BaseModel):
    rating: int = Field(
        ge=1,
        le=5,
        description="Rating of how good the context fits, from 1 (bad) to 5 (good)",
    )
    feedback: str = Field(
        description="Feedback on how the context fits with the pillars"
    )


# --- Schemas for improved pillar with explanations ---


class PillarChange(BaseModel):
    """Describes a specific change made to improve a pillar."""

    field: Literal["name", "description"] = Field(description="Which field was changed")
    after: str = Field(description="The new value after improvement")
    reasoning: str = Field(description="Why this change improves the pillar")
    issues_addressed: list[str] = Field(
        description="Which validation issues this change fixes (can be empty list)"
    )


class ImprovedPillarResponse(BaseModel):
    """Response containing improved pillar with explanations."""

    name: str = Field(description="Improved pillar name")
    description: str = Field(description="Improved pillar description")
    changes: list[PillarChange] = Field(
        description="List of changes made with explanations"
    )
    overall_summary: str = Field(
        description="High-level summary of why the improved pillar is better"
    )
    validation_issues_fixed: list[str] = Field(
        description="List of validation issue titles that were fixed"
    )
