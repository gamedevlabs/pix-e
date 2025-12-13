"""
Base context strategy interface.

All context engineering strategies implement this abstract base class,
providing a common interface for building and formatting context.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Protocol

from pxnodes.llm.context.base.types import (
    ContextResult,
    EvaluationScope,
    LayerContext,
    StrategyType,
)


class LLMProvider(Protocol):
    """
    Protocol for LLM provider interface.

    Any class implementing this protocol can be used for
    LLM-based operations (fact extraction, query refinement, etc.).
    """

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


class BaseContextStrategy(ABC):
    """
    Abstract base class for context engineering strategies.

    All strategies implement this interface for:
    1. Building context for evaluation
    2. Retrieving relevant information
    3. Formatting context for LLM prompts

    Strategies differ in HOW they retrieve and organize context:
    - Structural Memory: Vector retrieval of triples/facts
    - Hierarchical Graph: Deterministic graph traversal
    - H-MEM: Hierarchical vector retrieval with index routing
    - Combined: Structural data + H-MEM organization
    """

    strategy_type: StrategyType

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        **kwargs: Any,
    ):
        """
        Initialize the strategy.

        Args:
            llm_provider: Optional LLM for operations requiring generation
            **kwargs: Strategy-specific configuration
        """
        self.llm_provider = llm_provider
        self._config = kwargs

    @abstractmethod
    def build_context(
        self,
        scope: EvaluationScope,
        query: Optional[str] = None,
    ) -> ContextResult:
        """
        Build context for evaluation.

        This is the main entry point for generating context.
        Implementations should:
        1. Gather relevant information based on the scope
        2. Organize it according to the strategy's approach
        3. Format it for LLM consumption

        Args:
            scope: What to evaluate (target node, chart, project context)
            query: Optional query string for retrieval-based strategies

        Returns:
            ContextResult with formatted context and metadata
        """
        pass

    @abstractmethod
    def get_layer_context(
        self,
        scope: EvaluationScope,
        layer: int,
    ) -> LayerContext:
        """
        Get context at a specific hierarchy layer (1-4).

        For hierarchical strategies (2-4), this returns the context
        at a specific level:
        - L1 (Domain): Project-level (Pillars, Game Concept)
        - L2 (Category): Chart-level (Arc summary)
        - L3 (Trace): Path-level (State accumulation)
        - L4 (Episode): Node-level (Target + neighbors)

        For non-hierarchical strategies (1), this may return
        a synthetic layer based on the available data.

        Args:
            scope: What to evaluate
            layer: Layer number (1-4)

        Returns:
            LayerContext with content for that layer
        """
        pass

    def format_for_prompt(self, result: ContextResult) -> str:
        """
        Format context result for LLM prompt.

        Default implementation returns the context_string directly.
        Subclasses can override for custom formatting.

        Args:
            result: The context result to format

        Returns:
            Formatted string for LLM prompt
        """
        return result.context_string

    @property
    def requires_embeddings(self) -> bool:
        """
        Whether this strategy requires vector embeddings.

        Returns True for strategies that use vector similarity search
        (Structural Memory, H-MEM, Combined).

        Returns:
            True if embeddings are required
        """
        return False

    @property
    def requires_llm(self) -> bool:
        """
        Whether this strategy requires LLM for context building.

        Returns True for strategies that use LLM during context
        building (e.g., for fact extraction, query refinement).

        Returns:
            True if LLM is required
        """
        return False

    @property
    def is_hierarchical(self) -> bool:
        """
        Whether this strategy produces hierarchical (L1-L4) context.

        Returns:
            True if strategy produces layered context
        """
        return self.strategy_type in (
            StrategyType.HIERARCHICAL_GRAPH,
            StrategyType.HMEM,
            StrategyType.COMBINED,
        )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"strategy_type={self.strategy_type.value}, "
            f"requires_embeddings={self.requires_embeddings}, "
            f"requires_llm={self.requires_llm})"
        )
