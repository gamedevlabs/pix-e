"""
Aggregated SPARC response schemas.

Contains schemas for comprehensive evaluation responses that combine
multiple aspects with consistency checking and synthesis.
"""

from typing import List

from pydantic import BaseModel, Field

from sparc.llm.schemas.gameplay import GameplayResponse, GoalsChallengesRewardsResponse
from sparc.llm.schemas.player_experience import (
    PlayerExperienceResponse,
    PurposeResponse,
    ThemeResponse,
)
from sparc.llm.schemas.visual_meta import (
    ArtDirectionResponse,
    OpportunitiesRisksResponse,
    UniqueFeaturesResponse,
)
from sparc.llm.schemas.world import PlaceResponse, StoryNarrativeResponse


class AspectScore(BaseModel):
    """Score and metadata for a single SPARC aspect."""

    aspect: str = Field(description="Aspect name")
    score: int = Field(ge=0, le=100, description="Completeness score (0-100)")
    status: str = Field(description="Status: strong, adequate, weak, missing")
    key_issues: List[str] = Field(description="Top issues for this aspect")
    priority: str = Field(
        description="Priority for improvement: critical, high, medium, low"
    )


class ConsistencyIssue(BaseModel):
    """A consistency issue found between SPARC aspects."""

    aspects_involved: List[str] = Field(
        description="Which aspects have the inconsistency"
    )
    issue_type: str = Field(
        description=(
            "Type of inconsistency (contradiction, misalignment, missing_link)"
        )
    )
    description: str = Field(description="Description of the consistency issue")
    severity: str = Field(description="Severity: critical, high, medium, low")
    suggested_resolution: str = Field(description="How to resolve the inconsistency")


class SPARCQuickScanResponse(BaseModel):
    """
    Response for quick scan evaluation (all 10 aspects in parallel).

    Provides overview of all aspects with scores and basic feedback.
    """

    readiness_score: int = Field(
        ge=0, le=100, description="Overall prototype readiness score (0-100)"
    )
    readiness_status: str = Field(
        description="Ready, Nearly Ready, Needs Work, Not Ready"
    )
    aspect_scores: List[AspectScore] = Field(description="Scores for all 10 aspects")
    strongest_aspects: List[str] = Field(description="Top 3 strongest aspects")
    weakest_aspects: List[str] = Field(description="Top 3 weakest aspects")
    critical_gaps: List[str] = Field(description="Critical gaps that must be addressed")
    estimated_time_to_ready: str = Field(
        description="Estimated time to prototype-ready (e.g., '6-8 hours')"
    )
    next_steps: List[str] = Field(description="Prioritized list of next steps (top 5)")

    # Full aspect results
    player_experience: PlayerExperienceResponse
    theme: ThemeResponse
    gameplay: GameplayResponse
    place: PlaceResponse
    unique_features: UniqueFeaturesResponse
    story_narrative: StoryNarrativeResponse
    goals_challenges_rewards: GoalsChallengesRewardsResponse
    art_direction: ArtDirectionResponse
    purpose: PurposeResponse
    opportunities_risks: OpportunitiesRisksResponse


class SPARCComprehensiveResponse(BaseModel):
    """
    Response for comprehensive evaluation with consistency checking.

    Includes all quick scan data plus consistency analysis and synthesis.
    """

    # Include all quick scan data
    quick_scan: SPARCQuickScanResponse = Field(
        description="Complete quick scan results"
    )

    # Additional comprehensive analysis
    consistency_issues: List[ConsistencyIssue] = Field(
        description="Consistency issues found between aspects"
    )
    dependency_analysis: dict = Field(
        description="Which aspects depend on or inform other aspects"
    )
    synthesis: str = Field(description="Comprehensive synthesis of all evaluations")
    action_plan: List[dict] = Field(
        description=("Detailed action plan: {step, aspect, priority, estimated_time}")
    )
    strengths_summary: str = Field(description="Summary of concept's key strengths")
    weaknesses_summary: str = Field(description="Summary of concept's key weaknesses")
    recommendation: str = Field(
        description="Overall recommendation (proceed, iterate, rethink)"
    )


class MonolithicSPARCResponse(BaseModel):
    """
    Response from monolithic SPARC evaluation (baseline).

    Single-shot evaluation covering all aspects in one LLM call.
    """

    overall_assessment: str = Field(
        description="Overall assessment of game concept readiness"
    )
    aspects_evaluated: dict = Field(
        description="Brief evaluation of each aspect: {aspect_name: assessment}"
    )
    missing_aspects: List[str] = Field(description="Aspects not adequately addressed")
    suggestions: List[str] = Field(description="2-5 suggestions for improvement")
    additional_details: List[str] = Field(
        description="Additional details to make concept better"
    )
    readiness_verdict: str = Field(
        description="Ready to start development / Needs more work"
    )
