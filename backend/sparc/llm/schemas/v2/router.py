"""
Router agent schemas for SPARC V2.

The router extracts relevant portions of the game concept for each aspect.
"""

from typing import List

from pydantic import BaseModel, Field


class AspectExtraction(BaseModel):
    """
    Extraction for a single aspect.

    Contains the relevant text sections from the game concept
    that pertain to this specific aspect.
    """

    aspect_name: str = Field(
        description="Name of the aspect (e.g., 'player_experience', 'gameplay')"
    )
    extracted_sections: List[str] = Field(
        default_factory=list,
        description=(
            "Relevant text sections for this aspect. "
            "Empty list if aspect is not mentioned in the game concept."
        ),
    )


class RouterResponse(BaseModel):
    """
    Router agent output.

    Contains extractions for all requested aspects.
    """

    extractions: List[AspectExtraction] = Field(
        description="List of aspect extractions"
    )

    def get_extraction(self, aspect_name: str) -> AspectExtraction | None:
        """Get extraction for a specific aspect."""
        for extraction in self.extractions:
            if extraction.aspect_name == aspect_name:
                return extraction
        return None

    def has_content(self, aspect_name: str) -> bool:
        """Check if an aspect has any extracted content."""
        extraction = self.get_extraction(aspect_name)
        if extraction is None:
            return False
        return len(extraction.extracted_sections) > 0
