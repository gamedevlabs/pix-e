"""
LLM Adapter for Structural Memory Context.

Adapts the LLM Orchestrator/ModelManager to work with the
structural memory system's LLMProvider protocol.
"""

import logging
from typing import Any, Optional

import logfire

from llm.providers import ModelManager

logger = logging.getLogger(__name__)


class LLMProviderAdapter:
    """
    Adapter that makes ModelManager compatible with structural memory's
    LLMProvider protocol.

    This allows us to use the existing LLM orchestrator infrastructure
    for generating atomic facts and knowledge triples.
    """

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        model_name: Optional[str] = None,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM adapter.

        Args:
            model_manager: ModelManager instance (creates new one if not provided)
            model_name: Specific model to use (auto-selects if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.model_manager = model_manager or ModelManager()
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0

        # Auto-select model if not specified
        if not self.model_name:
            available_models = self.model_manager.list_available_models()
            if available_models:
                self.model_name = available_models[0].name
                logger.info(f"Auto-selected model: {self.model_name}")
            else:
                raise RuntimeError("No models available")

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text from prompt (implements LLMProvider protocol).

        Args:
            prompt: The prompt to generate from
            **kwargs: Additional generation parameters

        Returns:
            Generated text
        """
        # Extract parameters, preferring kwargs over instance defaults
        operation = kwargs.pop("operation", None)
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        model_name = kwargs.get("model_name", self.model_name)

        # Ensure model_name is not None
        if model_name is None:
            raise ValueError(
                "model_name must be provided either in kwargs or "
                "during initialization"
            )

        span_name = f"llm.generate.{operation}" if operation else "llm.generate"
        with logfire.span(
            span_name,
            model=model_name,
            temperature=temperature,
            prompt_length=len(prompt),
        ):
            try:
                result = self.model_manager.generate_with_model(
                    model_name=model_name,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                self.last_prompt_tokens = result.prompt_tokens
                self.last_completion_tokens = result.completion_tokens
                self.last_total_tokens = result.total_tokens

                logfire.info(
                    "llm.generate.complete",
                    model=result.model,
                    provider=result.provider,
                    response_length=len(result.text),
                )

                return result.text

            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                logfire.error(
                    "llm.generate.failed",
                    error=str(e),
                    model=model_name,
                    prompt_preview=prompt[:200],
                )
                raise


# Convenience function to create adapter with specific model
def create_llm_provider(
    model_name: Optional[str] = None,
    temperature: float = 0,
) -> LLMProviderAdapter:
    """
    Create an LLM provider adapter.

    Args:
        model_name: Specific model to use (auto-selects if None)
        temperature: Sampling temperature

    Returns:
        LLMProviderAdapter instance
    """
    return LLMProviderAdapter(
        model_name=model_name,
        temperature=temperature,
    )
