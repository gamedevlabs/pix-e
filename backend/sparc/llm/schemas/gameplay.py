"""
Gameplay-focused SPARC aspect schemas.

Contains schemas for gameplay mechanics and goals/challenges/rewards.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class GameplayResponse(BaseModel):
    """
    Gameplay evaluation response.

    Evaluates core gameplay mechanics, verbs, and the 30-second gameplay loop.
    """

    core_verbs: List[str] = Field(
        description=(
            "3-5 verbs that describe gameplay experience "
            "(explore, fight, build, etc.)"
        )
    )
    core_mechanics_identified: List[str] = Field(
        description="Core mechanics relevant to the idea"
    )
    thirty_second_gameplay: Optional[str] = Field(
        description="Description of what player does in 30 seconds of gameplay"
    )
    level_core_mechanics: List[str] = Field(
        description="Special level-specific core mechanics if applicable"
    )
    mechanics_clarity: int = Field(
        ge=0, le=100, description="How well-defined the core mechanics are (0-100)"
    )
    gameplay_loop_complete: bool = Field(
        description="Whether a complete gameplay loop is described"
    )
    missing_mechanics: List[str] = Field(
        description="Important mechanics that need definition"
    )
    suggestions: List[str] = Field(
        description="Suggestions for improving gameplay definition"
    )


class GoalsChallengesRewardsResponse(BaseModel):
    """
    Goals, Challenges & Rewards evaluation response.

    Evaluates objectives, obstacles, and reward structures.
    """

    objectives: List[dict] = Field(
        description="List of objectives: {description, start_point, end_point}"
    )
    obstacles: List[dict] = Field(
        description=(
            "List of obstacles per objective: " "{objective, obstacles, challenge_type}"
        )
    )
    rewards: List[dict] = Field(
        description="List of rewards: {objective, reward_type, description}"
    )
    story_integration: int = Field(
        ge=0,
        le=100,
        description="How well rewards integrate with story (0-100)",
    )
    communication_strategy: Optional[str] = Field(
        description="How objectives/obstacles/rewards are communicated"
    )
    challenge_balance: int = Field(
        ge=0, le=100, description="How balanced and appropriate challenges are (0-100)"
    )
    structure_completeness: int = Field(
        ge=0, le=100, description="How complete the goal structure is (0-100)"
    )
    missing_elements: List[str] = Field(
        description="Missing goal/challenge/reward elements"
    )
    suggestions: List[str] = Field(description="Suggestions for improvement")
