"""
Concrete SPARC context strategies.
"""

from typing import Any, Dict, Iterable, Optional

from sparc.llm.context.combined.strategy import (  # noqa: F401
    CombinedContextStrategy,
)
from sparc.llm.context.hmem.strategy import (  # noqa: F401
    HMemContextStrategy,
)
from sparc.llm.context.registry import ContextStrategyRegistry
from sparc.llm.context.strategy import BaseContextStrategy
from sparc.llm.context.structural_memory.strategy import (  # noqa: F401
    StructuralMemoryContextStrategy,
)
from sparc.llm.context.types import (
    AspectContext,
    AspectContextResult,
    ContextStrategyType,
)
from sparc.llm.schemas.v2.router import RouterResponse


@ContextStrategyRegistry.register(ContextStrategyType.ROUTER)
class RouterContextStrategy(BaseContextStrategy):
    """Use RouterAgent extractions as aspect context."""

    strategy_type = ContextStrategyType.ROUTER

    @property
    def requires_router(self) -> bool:
        return True

    async def build_aspect_contexts(
        self,
        data: Dict[str, Any],
        target_aspects: Iterable[str],
        router_response: Optional[RouterResponse] = None,
    ) -> AspectContextResult:
        if router_response is None:
            raise ValueError("router_response is required for router strategy")

        contexts: Dict[str, AspectContext] = {}
        for aspect_name in target_aspects:
            extraction = router_response.get_extraction(aspect_name)
            sections = extraction.extracted_sections if extraction else []
            contexts[aspect_name] = AspectContext(
                aspect_name=aspect_name,
                extracted_sections=sections,
            )

        return AspectContextResult(
            strategy=self.strategy_type,
            contexts=contexts,
        )


@ContextStrategyRegistry.register(ContextStrategyType.FULL_TEXT)
class FullTextContextStrategy(BaseContextStrategy):
    """Provide full game text to every aspect agent."""

    strategy_type = ContextStrategyType.FULL_TEXT

    async def build_aspect_contexts(
        self,
        data: Dict[str, Any],
        target_aspects: Iterable[str],
        router_response: Optional[RouterResponse] = None,
    ) -> AspectContextResult:
        game_text = data.get("game_text", "")
        contexts = {
            aspect_name: AspectContext(
                aspect_name=aspect_name,
                extracted_sections=[game_text] if game_text else [],
                metadata={"source": "full_text"},
            )
            for aspect_name in target_aspects
        }

        return AspectContextResult(
            strategy=self.strategy_type,
            contexts=contexts,
        )
