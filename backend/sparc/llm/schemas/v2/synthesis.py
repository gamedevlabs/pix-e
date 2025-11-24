"""
Synthesis agent schemas for SPARC V2.

The synthesis agent aggregates all aspect evaluations into a final report.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from sparc.llm.schemas.v2.aspects import SimplifiedAspectResponse


class SPARCSynthesis(BaseModel):
    """
    Synthesis of all aspect evaluations.

    Provides cross-aspect analysis and prioritized next steps.
    """

    overall_status: Literal["ready", "nearly_ready", "needs_work"] = Field(
        description=(
            "Overall prototype readiness. "
            "'ready': concept is well-defined across all key aspects. "
            "'nearly_ready': most aspects defined, minor gaps remain. "
            "'needs_work': significant gaps in concept definition."
        )
    )

    overall_reasoning: str = Field(
        description="2-3 sentence summary of overall concept state"
    )

    strongest_aspects: List[str] = Field(
        max_length=3, description="Top 3 best-defined aspects"
    )

    weakest_aspects: List[str] = Field(
        max_length=3, description="Top 3 aspects needing most work"
    )

    critical_gaps: List[str] = Field(
        description="Aspects that are blockers for prototyping"
    )

    next_steps: List[str] = Field(
        max_length=5, description="Prioritized actions to improve concept"
    )

    consistency_notes: Optional[str] = Field(
        default=None,
        description="Any cross-aspect inconsistencies or synergies identified",
    )


class SPARCV2Response(BaseModel):
    """
    Complete SPARC V2 evaluation response.

    Contains individual aspect results and the synthesis.
    """

    # Individual aspect results
    aspect_results: Dict[str, SimplifiedAspectResponse] = Field(
        description="Results for each evaluated aspect, keyed by aspect name"
    )

    # Synthesis (only present for full evaluation)
    synthesis: Optional[SPARCSynthesis] = Field(
        default=None, description="Cross-aspect synthesis (for full evaluation)"
    )

    # Metadata
    mode: str = Field(description="Evaluation mode: 'full', 'single', or 'multiple'")
    model_id: str = Field(description="Model used for evaluation")
    execution_time_ms: int = Field(description="Total execution time in milliseconds")
    total_tokens: int = Field(description="Total tokens used across all agents")
    estimated_cost_eur: float = Field(description="Estimated total cost in EUR")
