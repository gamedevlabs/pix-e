from pydantic import BaseModel, Field


class StringFeedback(BaseModel):
    feedback: str


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
    pillarId: int # Massive Security Risk, no time to worry about it
    name: str
    description: str


class ContradictionIssue(BaseModel):
    pillarOneId: int
    pillarTwoId: int
    pillarOneTitle: str
    pillarTwoTitle: str
    reason: str


class PillarCompletenessResponse(BaseModel):
    pillarFeedback: list[LLMPillar]


class PillarContradictionResponse(BaseModel):
    hasContradictions: bool
    contradictions: list[ContradictionIssue]


class PillarAdditionsFeedback(BaseModel):
    additions: list[LLMPillar] # ignore given pillarId, needs to be created by DB


class PillarsInContextResponse(BaseModel):
    coverage: PillarCompletenessResponse
    contradictions: PillarContradictionResponse
    proposedAdditions: PillarAdditionsFeedback

