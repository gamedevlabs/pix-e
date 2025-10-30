"""
Gameplay-focused SPARC aspect schemas.

Contains schemas for gameplay mechanics and goals/challenges/rewards.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(
        description="Suggestions for improving gameplay definition"
    )


class ObjectiveItem(BaseModel):
    """An objective in the game."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(description="Objective description")
    start_point: str = Field(description="Where the objective begins")
    end_point: str = Field(description="Where/how the objective completes")


class ObstacleItem(BaseModel):
    """Obstacles for an objective."""

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(description="Which objective this relates to")
    obstacles: List[str] = Field(description="List of obstacles for this objective")
    challenge_type: str = Field(description="Type of challenge presented")


class RewardItem(BaseModel):
    """Reward for completing an objective."""

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(description="Which objective this reward is for")
    reward_type: str = Field(description="Type of reward (intrinsic, extrinsic, etc.)")
    description: str = Field(description="Description of the reward")


class GoalsChallengesRewardsResponse(BaseModel):
    """
    Goals, Challenges & Rewards evaluation response.

    Evaluates objectives, obstacles, and reward structures.
    """

    objectives: List[ObjectiveItem] = Field(description="List of objectives")
    obstacles: List[ObstacleItem] = Field(description="List of obstacles per objective")
    rewards: List[RewardItem] = Field(description="List of rewards")
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
    score: int = Field(
        ge=0,
        le=100,
        description="Overall completeness score for this aspect (0-100)",
    )
    suggestions: List[str] = Field(description="Suggestions for improvement")
