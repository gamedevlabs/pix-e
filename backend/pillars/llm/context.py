"""
Context builder for Pillars evaluation strategies.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from game_concept.models import GameConcept
from pillars.models import Pillar
from pillars.utils import format_pillars_text


class PillarsContextStrategy(Enum):
    """Available context strategies for Pillars."""

    RAW = "raw"
    STRUCTURAL_MEMORY = "structural_memory"
    HMEM = "hmem"
    COMBINED = "combined"


@dataclass
class PillarsContextResult:
    """Resolved context payload for Pillars handlers."""

    pillars_text: str
    context_text: str
    strategy: PillarsContextStrategy
    metadata: dict[str, object] = field(default_factory=dict)


def build_pillars_context(
    pillars: List[Pillar],
    game_concept: GameConcept,
    strategy_name: Optional[str] = None,
) -> PillarsContextResult:
    """
    Build context payload for pillars handlers.

    This is the shared entry point for swapping strategies from the API layer.
    """
    try:
        strategy = (
            PillarsContextStrategy(strategy_name)
            if strategy_name
            else PillarsContextStrategy.RAW
        )
    except ValueError:
        strategy = PillarsContextStrategy.RAW

    pillars_text = format_pillars_text(pillars)
    context_text = game_concept.content

    metadata: dict[str, object] = {}
    if strategy != PillarsContextStrategy.RAW:
        metadata["strategy_warning"] = "non-raw strategies not implemented"

    return PillarsContextResult(
        pillars_text=pillars_text,
        context_text=context_text,
        strategy=strategy,
        metadata=metadata,
    )
