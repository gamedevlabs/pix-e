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
    evidence: List[str] = Field(
        default_factory=list,
        description="Concrete evidence references from context (node titles or quotes)",
    )
    unknowns: List[str] = Field(
        default_factory=list,
        description="Items that could not be verified due to missing context",
    )
    path_variance: str = Field(
        default="",
        description="Whether this assessment is consistent across paths "
        "or path-dependent",
    )


class BackwardCoherenceResult(CoherenceDimensionResult):
    """Result from backward coherence evaluation."""

    missing_prerequisites: List[str] = Field(
        default_factory=list,
        description="Items/abilities/mechanics required but not established",
    )
    satisfied_prerequisites: List[str] = Field(
        default_factory=list,
        description="Prerequisites that ARE properly established",
    )


class ForwardCoherenceResult(CoherenceDimensionResult):
    """Result from forward coherence evaluation."""

    elements_introduced: List[str] = Field(
        default_factory=list,
        description="New elements introduced that may be used later",
    )
    potential_payoffs: List[str] = Field(
        default_factory=list,
        description="How introduced elements might pay off in future nodes",
    )


class NodeIntegrityResult(CoherenceDimensionResult):
    """Result from node integrity evaluation."""

    contradictions: List[str] = Field(
        default_factory=list,
        description="Internal contradictions within the node",
    )
    unclear_elements: List[str] = Field(
        default_factory=list,
        description="Vague or unclear elements that need clarification",
    )


class GlobalFitResult(CoherenceDimensionResult):
    """Result from global fit evaluation (concept + pillars)."""

    pillar_alignment: List[str] = Field(
        default_factory=list,
        description="How the node aligns or conflicts with each pillar",
    )
    concept_alignment: str = Field(
        default="",
        description="Overall alignment with game concept and tone",
    )


class CoherenceAggregatedResult(BaseModel):
    """Aggregated result from all 4 coherence dimension agents."""

    node_id: str = Field(..., description="UUID of the evaluated node")
    node_name: str = Field(..., description="Name of the evaluated node")
    strategy_used: str = Field(..., description="Context strategy used for evaluation")

    # Individual dimension results
    backward_coherence: Optional[BackwardCoherenceResult] = None
    forward_coherence: Optional[ForwardCoherenceResult] = None
    global_fit: Optional[GlobalFitResult] = None
    node_integrity: Optional[NodeIntegrityResult] = None

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
        backward: Optional[BackwardCoherenceResult],
        forward: Optional[ForwardCoherenceResult],
        global_fit: Optional[GlobalFitResult],
        integrity: Optional[NodeIntegrityResult],
        execution_time_ms: int = 0,
        total_tokens: int = 0,
    ) -> "CoherenceAggregatedResult":
        """Build aggregated result from individual dimension results."""
        # Collect all scores and issues
        scores = []
        all_issues = []

        if backward:
            scores.append(backward.score)
            all_issues.extend(backward.issues)

        if forward:
            scores.append(forward.score)
            all_issues.extend(forward.issues)

        if integrity:
            scores.append(integrity.score)
            all_issues.extend(integrity.issues)

        if global_fit:
            scores.append(global_fit.score)
            all_issues.extend(global_fit.issues)

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 3.0

        # Identify critical issues (first 3 from lowest-scoring dimensions)
        critical_issues = all_issues[:3] if all_issues else []

        return cls(
            node_id=node_id,
            node_name=node_name,
            strategy_used=strategy_used,
            backward_coherence=backward,
            forward_coherence=forward,
            global_fit=global_fit,
            node_integrity=integrity,
            overall_score=round(overall_score, 2),
            is_coherent=overall_score >= 4.0,
            total_issues=len(all_issues),
            critical_issues=critical_issues,
            execution_time_ms=execution_time_ms,
            total_tokens=total_tokens,
        )
