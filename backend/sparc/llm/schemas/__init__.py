"""
SPARC response schemas.

Re-exports all schemas for easy importing.
"""

# Aggregated and supporting schemas
from sparc.llm.schemas.aggregated import (
    AspectScore,
    ConsistencyIssue,
    MonolithicSPARCResponse,
    SPARCComprehensiveResponse,
    SPARCQuickScanResponse,
)

# Individual aspect schemas - gameplay
from sparc.llm.schemas.gameplay import GameplayResponse, GoalsChallengesRewardsResponse

# Individual aspect schemas - player-focused
from sparc.llm.schemas.player_experience import (
    PlayerExperienceResponse,
    PurposeResponse,
    ThemeResponse,
)

# Individual aspect schemas - visual and meta
from sparc.llm.schemas.visual_meta import (
    ArtDirectionResponse,
    OpportunitiesRisksResponse,
    UniqueFeaturesResponse,
)

# Individual aspect schemas - world building
from sparc.llm.schemas.world import PlaceResponse, StoryNarrativeResponse

__all__ = [
    # Player-focused aspects
    "PlayerExperienceResponse",
    "ThemeResponse",
    "PurposeResponse",
    # Gameplay aspects
    "GameplayResponse",
    "GoalsChallengesRewardsResponse",
    # World building aspects
    "PlaceResponse",
    "StoryNarrativeResponse",
    # Visual and meta aspects
    "ArtDirectionResponse",
    "UniqueFeaturesResponse",
    "OpportunitiesRisksResponse",
    # Aggregated responses
    "SPARCQuickScanResponse",
    "SPARCComprehensiveResponse",
    "MonolithicSPARCResponse",
    # Supporting schemas
    "AspectScore",
    "ConsistencyIssue",
]
