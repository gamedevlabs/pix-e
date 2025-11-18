"""
Pydantic schemas for context data structures.

These schemas define the shape of context data passed between features
and used in LLM prompts.
"""

from pydantic import BaseModel


class PillarData(BaseModel):
    """Pillar data for context."""

    pass  # Pillar data coming soon


class SPARCData(BaseModel):
    """SPARC evaluation data for context."""

    pass  # SPARC data coming soon


class UserContext(BaseModel):
    """User context containing all relevant data."""

    pass  # User context coming soon


class CoherenceReport(BaseModel):
    """Coherence check report."""

    pass  # Coherence report coming soon
