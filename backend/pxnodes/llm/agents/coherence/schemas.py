"""
Schemas for coherence dimension agents.

Each agent produces a CoherenceDimensionResult with:
- score (1-6): Numeric score for statistical analysis
- reasoning: Detailed qualitative explanation
- issues: Specific problems identified
- suggestions: Improvement recommendations
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class CoherenceDimensionResult(BaseModel):
    """Result from a single coherence dimension evaluation."""

    score: int = Field(
        ...,
        ge=1,
        le=6,
        description="Coherence score from 1 (very poor) to 6 (excellent)",
    )
    reasoning: str = Field(
        ...,
        description="Detailed qualitative explanation of the score",
    )
    issues: List[str] = Field(
        default_factory=list,
        description="Specific problems identified in this dimension",
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Improvement recommendations for this dimension",
    )


class PrerequisiteAlignmentResult(CoherenceDimensionResult):
    """Result from prerequisite alignment evaluation."""

    missing_prerequisites: List[str] = Field(
        default_factory=list,
        description="Items/abilities/mechanics required but not established",
    )
    satisfied_prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites that ARE properly established",
    )


class ForwardSetupResult(CoherenceDimensionResult):
    """Result from forward setup evaluation."""

    elements_introduced: List[str] = Field(
        default_factory=list,
        description="New elements introduced that may be used later",
    )
    potential_payoffs: List[str] = Field(
        default_factory=list,
        description="How introduced elements might pay off in future nodes",
    )


class InternalConsistencyResult(CoherenceDimensionResult):
    """Result from internal consistency evaluation."""

    contradictions: List[str] = Field(
        default_factory=list,
        description="Internal contradictions within the node",
    )
    unclear_elements: List[str] = Field(
        default_factory=list,
        description="Vague or unclear elements that need clarification",
    )


class ContextualFitResult(CoherenceDimensionResult):
    """Result from contextual fit evaluation."""

    pillar_alignment: List[str] = Field(
        default_factory=list,
        description="How the node aligns with game design pillars",
    )
    concept_alignment: str = Field(
        default="",
        description="How the node fits the overall game concept",
    )


class CoherenceAggregatedResult(BaseModel):
    """Aggregated result from all 4 coherence dimension agents."""

    node_id: str = Field(..., description="UUID of the evaluated node")
    node_name: str = Field(..., description="Name of the evaluated node")
    strategy_used: str = Field(..., description="Context strategy used for evaluation")

    # Individual dimension results
    prerequisite_alignment: Optional[PrerequisiteAlignmentResult] = None
    forward_setup: Optional[ForwardSetupResult] = None
    internal_consistency: Optional[InternalConsistencyResult] = None
    contextual_fit: Optional[ContextualFitResult] = None

    # Aggregated metrics
    overall_score: float = Field(
        ...,
        ge=1.0,
        le=6.0,
        description="Average score across all dimensions",
    )
    is_coherent: bool = Field(
        ...,
        description="True if node passes coherence threshold (score >= 4)",
    )
    total_issues: int = Field(
        default=0,
        description="Total number of issues across all dimensions",
    )
    critical_issues: List[str] = Field(
        default_factory=list,
        description="Most critical issues requiring attention",
    )

    # Execution metadata
    execution_time_ms: int = Field(
        default=0,
        description="Total execution time in milliseconds",
    )
    total_tokens: int = Field(
        default=0,
        description="Total tokens used across all agents",
    )

    @classmethod
    def from_dimension_results(
        cls,
        node_id: str,
        node_name: str,
        strategy_used: str,
        prerequisite: Optional[PrerequisiteAlignmentResult],
        forward: Optional[ForwardSetupResult],
        internal: Optional[InternalConsistencyResult],
        contextual: Optional[ContextualFitResult],
        execution_time_ms: int = 0,
        total_tokens: int = 0,
    ) -> "CoherenceAggregatedResult":
        """Build aggregated result from individual dimension results."""
        # Collect all scores and issues
        scores = []
        all_issues = []

        if prerequisite:
            scores.append(prerequisite.score)
            all_issues.extend(prerequisite.issues)

        if forward:
            scores.append(forward.score)
            all_issues.extend(forward.issues)

        if internal:
            scores.append(internal.score)
            all_issues.extend(internal.issues)

        if contextual:
            scores.append(contextual.score)
            all_issues.extend(contextual.issues)

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 3.0

        # Identify critical issues (first 3 from lowest-scoring dimensions)
        critical_issues = all_issues[:3] if all_issues else []

        return cls(
            node_id=node_id,
            node_name=node_name,
            strategy_used=strategy_used,
            prerequisite_alignment=prerequisite,
            forward_setup=forward,
            internal_consistency=internal,
            contextual_fit=contextual,
            overall_score=round(overall_score, 2),
            is_coherent=overall_score >= 4.0,
            total_issues=len(all_issues),
            critical_issues=critical_issues,
            execution_time_ms=execution_time_ms,
            total_tokens=total_tokens,
        )
