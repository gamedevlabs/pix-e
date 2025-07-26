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

class ContradictionIssue(BaseModel):
    pillarOneTitle: str
    pillarTwoTitle: str
    reason: str


class LLMPillar(BaseModel):
    pillarId: int
    name: str
    description: str


class PillarsInContextResponse(BaseModel):
    proposedAdditions: list[LLMPillar]
    ideaIssues: list[LLMPillar]
    contradictions: list[ContradictionIssue]

