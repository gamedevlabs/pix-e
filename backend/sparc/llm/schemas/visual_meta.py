"""
Visual and meta SPARC aspect schemas.

Contains schemas for art direction, unique features, and opportunities/risks.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ColorPalette(BaseModel):
    """Color palette for the game."""

    model_config = ConfigDict(extra="forbid")

    primary: str = Field(description="Primary color")
    secondary: str = Field(description="Secondary color")
    light_source: str = Field(description="Light source color")
    shadow_color: str = Field(description="Shadow color")


class ArtDirectionResponse(BaseModel):
    """
    Art Direction evaluation response.

    Evaluates art style, visual uniqueness, and color palette.
    """

    art_style: Optional[str] = Field(
        description="Art style (realistic, stylized, cartoonish, etc.)"
    )
    visual_uniqueness_elements: List[str] = Field(
        description="2-3 things that make project visually unique"
    )
    color_palette: Optional[ColorPalette] = Field(
        description="Color palette with primary, secondary, light_source, shadow_color"
    )
    lighting_ratio: Optional[str] = Field(
        description="Light vs dark ratio (high-contrast, evenly lit, etc.)"
    )
    temperature: Optional[str] = Field(description="Warm or cool color palette")
    reference_suggestions: List[str] = Field(
        description="Suggested reference games/projects for mood boards"
    )
    art_direction_completeness: int = Field(
        ge=0, le=100, description="How complete the art direction is (0-100)"
    )
    style_clarity: int = Field(
        ge=0, le=100, description="How clear the art style definition is (0-100)"
    )
    missing_elements: List[str] = Field(description="Missing art direction elements")
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(
        description="Suggestions for art direction development"
    )


class UniquenessItem(BaseModel):
    """Validation of a unique feature claim."""

    model_config = ConfigDict(extra="forbid")

    feature: str = Field(description="The claimed unique feature")
    is_unique: bool = Field(description="Whether this feature is truly unique")
    reasoning: str = Field(description="Reasoning for the uniqueness assessment")


class UniqueFeaturesResponse(BaseModel):
    """
    Unique Features evaluation response.

    Evaluates how the idea is unique and different from existing projects.
    """

    claimed_unique_features: List[str] = Field(
        description="Unique features claimed in the game text"
    )
    validated_uniqueness: List[UniquenessItem] = Field(
        description="Each feature with validation of uniqueness"
    )
    differentiation_from_existing: str = Field(
        description="How idea differs from other projects"
    )
    genre_improvements: List[str] = Field(
        description="How it improves upon existing genre/location/theme"
    )
    defining_elements: List[str] = Field(
        description="3-5 features that will be defining elements"
    )
    uniqueness_score: int = Field(
        ge=0, le=100, description="Overall uniqueness score (0-100)"
    )
    needs_validation: List[str] = Field(
        description="Uniqueness claims that need evidence/validation"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(
        description="Suggestions for strengthening uniqueness"
    )


class OpportunityItem(BaseModel):
    """An opportunity for the game concept."""

    model_config = ConfigDict(extra="forbid")

    opportunity: str = Field(description="The opportunity identified")
    description: str = Field(description="Description of the opportunity")
    how_to_use: str = Field(description="How to leverage this opportunity")


class RiskItem(BaseModel):
    """A risk for the game concept."""

    model_config = ConfigDict(extra="forbid")

    risk: str = Field(description="The risk identified")
    likelihood: str = Field(description="Likelihood of risk (low, medium, high)")
    impact: str = Field(description="Impact if risk occurs (low, medium, high)")
    mitigation: str = Field(description="How to mitigate this risk")


class OpportunitiesRisksResponse(BaseModel):
    """
    Opportunities & Risks evaluation response.

    Evaluates opportunities for success and potential risks with mitigations.
    """

    opportunities: List[OpportunityItem] = Field(description="List of opportunities")
    risks: List[RiskItem] = Field(description="List of risks")
    opportunity_score: int = Field(
        ge=0, le=100, description="Overall opportunity strength (0-100)"
    )
    risk_score: int = Field(
        ge=0, le=100, description="Overall risk level (0-100, higher = riskier)"
    )
    risk_mitigation_completeness: int = Field(
        ge=0, le=100, description="How well risks are mitigated (0-100)"
    )
    critical_risks: List[str] = Field(
        description="High-likelihood or high-impact risks needing attention"
    )
    missing_analysis: List[str] = Field(description="Missing opportunity/risk analysis")
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(description="Suggestions for risk management")
