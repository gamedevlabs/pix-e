"""
Strategy registry for context engineering strategies.

Provides a central registry for registering and retrieving
context strategies by type.
"""

import logging
from typing import Any, Optional, Type

from pxnodes.llm.context.base.strategy import BaseContextStrategy, LLMProvider
from pxnodes.llm.context.base.types import StrategyType

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """
    Registry for context engineering strategies.

    Follows the same pattern as the existing handler_registry
    in the LLM orchestrator.

    Usage:
        # Registration (via decorator)
        @StrategyRegistry.register(StrategyType.STRUCTURAL_MEMORY)
        class StructuralMemoryStrategy(BaseContextStrategy):
            ...

        # Creation
        strategy = StrategyRegistry.create(
            StrategyType.STRUCTURAL_MEMORY,
            llm_provider=my_provider
        )
    """

    _strategies: dict[StrategyType, Type[BaseContextStrategy]] = {}

    @classmethod
    def register(cls, strategy_type: StrategyType):
        """
        Decorator to register a strategy class.

        Args:
            strategy_type: The type to register this strategy under

        Returns:
            Decorator function
        """

        def decorator(strategy_class: Type[BaseContextStrategy]):
            if strategy_type in cls._strategies:
                logger.warning(
                    f"Overwriting existing strategy registration for {strategy_type}"
                )
            cls._strategies[strategy_type] = strategy_class
            strategy_class.strategy_type = strategy_type
            logger.debug(f"Registered strategy: {strategy_type.value}")
            return strategy_class

        return decorator

    @classmethod
    def get(cls, strategy_type: StrategyType) -> Type[BaseContextStrategy]:
        """
        Get a strategy class by type.

        Args:
            strategy_type: The strategy type to retrieve

        Returns:
            The strategy class

        Raises:
            ValueError: If strategy type is not registered
        """
        if strategy_type not in cls._strategies:
            available = [s.value for s in cls._strategies.keys()]
            raise ValueError(
                f"Unknown strategy: {strategy_type.value}. " f"Available: {available}"
            )
        return cls._strategies[strategy_type]

    @classmethod
    def create(
        cls,
        strategy_type: StrategyType,
        llm_provider: Optional[LLMProvider] = None,
        **kwargs: Any,
    ) -> BaseContextStrategy:
        """
        Create a strategy instance.

        Args:
            strategy_type: The strategy type to create
            llm_provider: Optional LLM provider for strategies that need it
            **kwargs: Strategy-specific configuration

        Returns:
            Configured strategy instance
        """
        strategy_class = cls.get(strategy_type)
        return strategy_class(llm_provider=llm_provider, **kwargs)

    @classmethod
    def list_strategies(cls) -> list[StrategyType]:
        """
        List all registered strategy types.

        Returns:
            List of registered strategy types
        """
        return list(cls._strategies.keys())

    @classmethod
    def list_strategy_info(cls) -> list[dict[str, Any]]:
        """
        List all strategies with their metadata.

        Useful for API endpoints that need to show available options.

        Returns:
            List of strategy info dictionaries
        """
        result = []
        for strategy_type, strategy_class in cls._strategies.items():
            # Create a temporary instance to get properties
            # (without LLM provider since we just want metadata)
            try:
                temp_instance = strategy_class()
                info = {
                    "id": strategy_type.value,
                    "name": strategy_type.name,
                    "class": strategy_class.__name__,
                    "requires_embeddings": temp_instance.requires_embeddings,
                    "requires_llm": temp_instance.requires_llm,
                    "is_hierarchical": temp_instance.is_hierarchical,
                    "docstring": strategy_class.__doc__,
                }
            except Exception:
                # Fallback if instance creation fails
                info = {
                    "id": strategy_type.value,
                    "name": strategy_type.name,
                    "class": strategy_class.__name__,
                }
            result.append(info)
        return result

    @classmethod
    def is_registered(cls, strategy_type: StrategyType) -> bool:
        """
        Check if a strategy type is registered.

        Args:
            strategy_type: The strategy type to check

        Returns:
            True if registered
        """
        return strategy_type in cls._strategies

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered strategies.

        Primarily for testing purposes.
        """
        cls._strategies.clear()


def get_strategy(
    strategy_type: str | StrategyType,
    llm_provider: Optional[LLMProvider] = None,
    **kwargs: Any,
) -> BaseContextStrategy:
    """
    Convenience function to get a strategy instance.

    Accepts either a StrategyType enum or string.

    Args:
        strategy_type: Strategy type (enum or string)
        llm_provider: Optional LLM provider
        **kwargs: Strategy-specific configuration

    Returns:
        Configured strategy instance
    """
    if isinstance(strategy_type, str):
        strategy_type = StrategyType(strategy_type)
    return StrategyRegistry.create(strategy_type, llm_provider=llm_provider, **kwargs)
