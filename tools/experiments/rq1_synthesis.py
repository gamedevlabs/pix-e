from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError


class RQ1Synthesis(BaseModel):
    overall_status: str = Field(description="ready | nearly_ready | needs_work")
    overall_reasoning: str = Field(
        description="2-3 sentence summary of the concept evaluation"
    )
    strongest_aspects: List[str] = Field(
        default_factory=list, description="Top 3 strongest aspects"
    )
    weakest_aspects: List[str] = Field(
        default_factory=list, description="Top 3 weakest aspects"
    )
    critical_gaps: List[str] = Field(
        default_factory=list, description="Key gaps blocking prototyping"
    )
    next_steps: List[str] = Field(
        default_factory=list, description="Prioritized actions to improve concept"
    )
    consistency_notes: Optional[str] = Field(
        default=None, description="Cross-aspect inconsistencies or synergies"
    )


def run_rq1_synthesis(
    *,
    model_name: str,
    mode: str,
    results: Dict[str, Any],
) -> Dict[str, Any]:
    _ = model_name
    if mode == "monolithic":
        data = results or {}
    else:
        data = (results or {}).get("synthesis", {})

    if not data:
        return {}

    try:
        return RQ1Synthesis(**data).model_dump()
    except ValidationError:
        return data
