"""
Registry for SPARC context strategies.
"""

from typing import Dict, Type

from sparc.llm.context.strategy import BaseContextStrategy
from sparc.llm.context.types import ContextStrategyType


class ContextStrategyRegistry:
    """Registry for SPARC context strategies."""

    _strategies: Dict[ContextStrategyType, Type[BaseContextStrategy]] = {}

    @classmethod
    def register(
        cls, strategy_type: ContextStrategyType
    ):  # noqa: ANN201 - decorator signature
        """Register a strategy class."""

        def decorator(
            strategy_cls: Type[BaseContextStrategy],
        ) -> Type[BaseContextStrategy]:
            cls._strategies[strategy_type] = strategy_cls
            return strategy_cls

        return decorator

    @classmethod
    def create(
        cls,
        strategy_type: ContextStrategyType,
        **kwargs: object,
    ) -> BaseContextStrategy:
        """Instantiate a registered strategy."""
        strategy_cls = cls._strategies.get(strategy_type)
        if not strategy_cls:
            raise ValueError(f"Unsupported context strategy: {strategy_type.value}")
        return strategy_cls(**kwargs)
