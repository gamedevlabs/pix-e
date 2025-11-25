"""
Document Context Agent response schema for SPARC V2.
"""

from typing import List

from pydantic import BaseModel, Field


class AspectDocumentExtraction(BaseModel):
    """Document content extracted for a specific aspect."""

    aspect_name: str = Field(
        description="The SPARC aspect name (e.g., 'player_experience')"
    )
    extracted_sections: List[str] = Field(
        description="Relevant sections from the document for this aspect",
        default_factory=list,
    )
    key_insights: List[str] = Field(
        description="Key insights, constraints, or design decisions from the document",
        default_factory=list,
    )


class DocumentContextResponse(BaseModel):
    """Response from Document Context Agent."""

    extractions: List[AspectDocumentExtraction] = Field(
        description="Document content organized by aspect"
    )
    document_summary: str = Field(
        description="Brief summary of what the design document covers"
    )
