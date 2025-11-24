"""
Pillar Context schemas for SPARC V2.

Provides pillar context to aspect agents for alignment checking.
"""

from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class PillarContextResponse(BaseModel):
    """
    Response from PillarContextAgent.

    Contains pillar information formatted for aspect agent consumption.
    """

    mode: Literal["all", "filtered"] = Field(
        description="Mode used for pillar assignment"
    )

    pillars_available: bool = Field(
        description="Whether any pillars were found for the user"
    )

    all_pillars_text: str = Field(
        default="",
        description="All pillars formatted as '[ID: X] Name: desc' list",
    )

    filtered_assignments: Dict[str, List[int]] = Field(
        default_factory=dict,
        description=(
            "Mapping of aspect names to relevant pillar IDs. "
            "Only populated in 'filtered' mode."
        ),
    )

    pillars_count: int = Field(
        default=0, description="Total number of pillars available"
    )
