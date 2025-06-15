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


class FixablePillar(BaseModel):
    name: str
    description: str
