"""
Pydantic schemas for context data structures.

These schemas define the shape of context data passed between features
and used in LLM prompts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PillarData(BaseModel):
    """Pillar data for context."""

    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class SPARCData(BaseModel):
    """SPARC evaluation data for context."""

    id: int
    overall_score: float
    readiness_status: str
    aspect_results: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class UserContext(BaseModel):
    """
    User context containing all relevant data.

    This is the main context object passed to handlers and prompts.
    """

    game_concept: Optional[str] = None
    pillars: List[PillarData] = Field(default_factory=list)
    sparc_evaluation: Optional[SPARCData] = None
    last_updated: Dict[str, datetime] = Field(default_factory=dict)

    class Config:
        from_attributes = True


class CoherenceReport(BaseModel):
    """
    Coherence check report.

    Contains information about coherence issues and suggestions.
    """

    is_coherent: bool
    severity: str = Field(..., description="none | minor | major")
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    affected_features: List[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
