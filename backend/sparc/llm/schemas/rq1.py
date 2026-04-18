"""
Unified RQ1 experiment response schema.

All three orchestration modes (monolithic, agentic full-text, agentic routed)
must produce this exact schema for apples-to-apples comparison.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from sparc.llm.schemas.v2.aspects import SimplifiedAspectResponse
from sparc.llm.schemas.v2.synthesis import SPARCSynthesis

SPARC_ASPECT_NAMES = [
    "player_experience",
    "theme",
    "purpose",
    "gameplay",
    "goals_challenges_rewards",
    "place",
    "story_narrative",
    "unique_features",
    "art_direction",
    "opportunities_risks",
]


class RQ1UnifiedResponse(BaseModel):
    """
    Unified response schema for RQ1 experiment.

    All three orchestration modes produce this schema natively:
    - Monolithic: single LLM call returning this structure
    - Agentic full-text: assembled from 10 aspect agents + synthesis agent
    - Agentic routed: assembled from router + 10 aspect agents + synthesis agent
    """

    aspect_results: Dict[str, SimplifiedAspectResponse]
    synthesis: SPARCSynthesis


class RQ1ModeResult(BaseModel):
    """Result from a single orchestration mode for one concept."""

    success: bool
    response: Optional[RQ1UnifiedResponse] = None
    execution_time_ms: int = Field(description="Wall-clock time in milliseconds")
    total_tokens: int = Field(description="Total tokens consumed across all LLM calls")
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    llm_calls: int = Field(description="Number of LLM calls made")
    estimated_cost_eur: float = Field(default=0.0)
    errors: List[str] = Field(default_factory=list)
