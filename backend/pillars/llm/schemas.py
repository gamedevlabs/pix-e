"""
Response schemas for pillar operations.

These Pydantic models define the structure of LLM responses.
All schemas are migrated from backend/llm/llm_links/responseSchemes.py to centralize
pillar-specific logic in the orchestrator.
"""

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
    pillarFeedback: list[CompletenessAnswer] = Field(
        description="Reasoning for each pillar"
    )


class PillarContradictionResponse(BaseModel):
    hasContradictions: bool
    contradictions: list[ContradictionIssue]


class PillarAdditionsFeedback(BaseModel):
    additions: list[LLMPillar]  # ignore given pillarId, needs to be created by DB


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
