"""
Base interface for SPARC context strategies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional

from sparc.llm.context.types import AspectContextResult, ContextStrategyType
from sparc.llm.schemas.v2.router import RouterResponse


class BaseContextStrategy(ABC):
    """Abstract base for SPARC context strategies."""

    strategy_type: ContextStrategyType

    def __init__(self, **kwargs: Any) -> None:
        self._config = kwargs

    @abstractmethod
    async def build_aspect_contexts(
        self,
        data: Dict[str, Any],
        target_aspects: Iterable[str],
        router_response: Optional[RouterResponse] = None,
    ) -> AspectContextResult:
        """Build aspect-specific context payloads."""
        raise NotImplementedError

    @property
    def requires_router(self) -> bool:
        """Whether this strategy depends on RouterAgent output."""
        return False

    def get_config(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""
        return self._config.get(key, default)
