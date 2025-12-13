"""
Base module for context engineering strategies.

Provides the common interface and types used by all strategies.
"""

from pxnodes.llm.context.base.registry import StrategyRegistry
from pxnodes.llm.context.base.strategy import BaseContextStrategy
from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
)

__all__ = [
    "BaseContextStrategy",
    "StrategyRegistry",
    "StrategyType",
    "ContextResult",
    "LayerContext",
    "EvaluationScope",
]
