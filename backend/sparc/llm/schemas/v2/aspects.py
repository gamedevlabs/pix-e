"""
Simplified aspect response schemas for SPARC V2.

All aspect agents use the same simplified response format.
"""

from typing import List, Literal

from pydantic import BaseModel, Field


class SimplifiedAspectResponse(BaseModel):
    """
    Simplified aspect evaluation response.

    Used by all 10 aspect agents for consistent output format.
    Binary status with reasoning and suggestions.
    """

    aspect_name: str = Field(description="Name of the aspect being evaluated")

    status: Literal["well_defined", "needs_work", "not_provided"] = Field(
        description=(
            "Assessment of aspect definition quality. "
            "'well_defined': aspect is clear and complete. "
            "'needs_work': aspect is vague, incomplete, or inconsistent. "
            "'not_provided': aspect was not addressed in the game concept."
        )
    )

    reasoning: str = Field(
        description="Explanation of why this status was assigned (2-3 sentences)"
    )

    suggestions: List[str] = Field(
        description=(
            "Concrete suggestions for improvement. "
            "Can include suggestions even for well_defined aspects. "
            "Use an empty list if no suggestions."
        ),
    )
