"""
World-building SPARC aspect schemas.

Contains schemas for place/environment and story/narrative aspects.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class PlaceResponse(BaseModel):
    """
    Place evaluation response.

    Evaluates the environment setting and key locations.
    """

    environment_setting: Optional[str] = Field(
        description="The environment setting for the game/level"
    )
    key_locations: List[str] = Field(
        description="Concrete key locations identified or suggested"
    )
    location_specificity: int = Field(
        ge=0,
        le=100,
        description="How specific and concrete the locations are (0-100)",
    )
    setting_clarity: int = Field(
        ge=0, le=100, description="How clear the environment setting is (0-100)"
    )
    location_variety: int = Field(
        ge=0,
        le=100,
        description="How diverse and interesting the locations are (0-100)",
    )
    missing_elements: List[str] = Field(
        description="Missing location or setting elements"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(
        description="Suggestions for developing place/locations"
    )


class StoryNarrativeResponse(BaseModel):
    """
    Story & Narrative evaluation response.

    Evaluates story structure, arrival, history, and key events.
    """

    story_summary: Optional[str] = Field(
        description="Brief summary of the story if present"
    )
    storytelling_methods: List[str] = Field(
        description=(
            "Methods used (environmental, cutscenes, gameplay, dialogue, etc.)"
        )
    )
    environment_description: Optional[str] = Field(
        description="Description from perspective of character/inhabitant"
    )
    history_before_arrival: Optional[str] = Field(
        description="What happened before player arrived"
    )
    player_arrival_how: Optional[str] = Field(
        description="How player arrives in location"
    )
    player_arrival_why: Optional[str] = Field(
        description="Why player travels to this place"
    )
    player_overall_goal: Optional[str] = Field(description="Overall goal of the player")
    communication_method: Optional[str] = Field(
        description="How arrival context is communicated to player"
    )
    navigation_flow: Optional[str] = Field(
        description="How player navigates through environment"
    )
    key_events: List[str] = Field(description="Key events player will experience")
    story_completeness: int = Field(
        ge=0, le=100, description="How complete the story structure is (0-100)"
    )
    missing_story_elements: List[str] = Field(
        description="Story elements that need development"
    )
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(description="Suggestions for story development")
