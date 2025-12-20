"""
SPARC context strategy entry points.
"""

from sparc.llm.context.registry import ContextStrategyRegistry
from sparc.llm.context.strategies import (  # noqa: F401
    CombinedContextStrategy,
    FullTextContextStrategy,
    HMemContextStrategy,
    RouterContextStrategy,
    StructuralMemoryContextStrategy,
)
from sparc.llm.context.strategy import BaseContextStrategy
from sparc.llm.context.types import ContextStrategyType


def get_context_strategy(
    strategy_name: str,
    **kwargs: object,
) -> BaseContextStrategy:
    """Resolve a strategy name to a strategy instance."""
    try:
        strategy_type = ContextStrategyType(strategy_name)
    except ValueError as exc:
        raise ValueError(f"Unknown SPARC context strategy: {strategy_name}") from exc

    return ContextStrategyRegistry.create(strategy_type, **kwargs)
