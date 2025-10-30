"""
Player-focused SPARC aspect schemas.

Contains schemas for aspects related to player experience, theme, and purpose.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PlayerExperienceResponse(BaseModel):
    """
    Player Experience evaluation response.

    Evaluates what the player will experience emotionally and creates
    a high concept statement for the game idea.
    """

    current_description: str = Field(
        description="The current player experience description from the game text"
    )
    is_player_active_form: bool = Field(
        description=(
            "Whether description uses player in active form "
            "('I do X' vs 'player does X')"
        )
    )
    emotional_focus_present: bool = Field(
        description="Whether description focuses on emotional experience"
    )
    emotional_keywords: List[str] = Field(
        description="Emotional keywords identified (tension, joy, triumph, etc.)"
    )
    improved_description: str = Field(
        description=(
            "Enhanced player experience description in active form "
            "with emotional focus"
        )
    )
    high_concept_statement: str = Field(
        description="Clear high concept statement for the game idea"
    )
    clarity_score: int = Field(
        ge=0,
        le=100,
        description="How clear and compelling the player experience is (0-100)",
    )
    issues: List[str] = Field(description="List of issues found in current description")
    suggestions: List[str] = Field(description="Actionable suggestions for improvement")


class ThemeResponse(BaseModel):
    """
    Theme evaluation response.

    Analyzes the dominant and secondary themes of the game concept.
    """

    dominant_theme: Optional[str] = Field(
        description="The main unifying theme identified"
    )
    dominant_theme_clarity: int = Field(
        ge=0, le=100, description="How clearly the dominant theme is defined (0-100)"
    )
    secondary_themes: List[str] = Field(
        description="List of secondary themes identified"
    )
    theme_consistency: int = Field(
        ge=0,
        le=100,
        description=("How consistently theme is expressed throughout concept (0-100)"),
    )
    missing_theme_elements: List[str] = Field(
        description="Theme elements that should be defined"
    )
    suggestions: List[str] = Field(description="Suggestions for strengthening theme")


class PurposeResponse(BaseModel):
    """
    Purpose evaluation response.

    Evaluates project purpose, personal motivation, and team appeal.
    """

    project_purpose: Optional[str] = Field(
        description="Purpose of the game/level project"
    )
    creator_motivation: Optional[str] = Field(
        description="Why creator wants to work on this"
    )
    team_appeal: Optional[str] = Field(
        description="Why others would want to work on this"
    )
    creator_goals: Optional[str] = Field(description="What creator wants to achieve")
    purpose_clarity: int = Field(
        ge=0, le=100, description="How clearly purpose is defined (0-100)"
    )
    motivation_strength: int = Field(
        ge=0, le=100, description="How strong and clear the motivation is (0-100)"
    )
    missing_elements: List[str] = Field(
        description="Missing purpose/motivation elements"
    )
    suggestions: List[str] = Field(description="Suggestions for clarifying purpose")
