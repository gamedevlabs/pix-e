"""
Utility functions for pillar operations.

Includes LLM call tracking and cost calculation.
"""

from typing import Optional

from django.contrib.auth.models import User

from llm.types import LLMResponse

from .models import Pillar, PillarLLMCall

# Model pricing per 1M tokens (EUR)
MODEL_COSTS = {
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free tier
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gpt-4o-mini": {"input": 0.135, "output": 0.540},
    "gpt-4o": {"input": 2.25, "output": 9.00},
    "gpt-4-turbo": {"input": 9.00, "output": 27.00},
}


def calculate_cost_eur(
    model_name: str, prompt_tokens: int = 0, completion_tokens: int = 0
) -> float:
    """
    Calculate cost in EUR based on token usage and model pricing.

    Args:
        model_name: The model identifier
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens

    Returns:
        Estimated cost in EUR (rounded to 8 decimal places)
    """
    costs = MODEL_COSTS.get(model_name, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * costs["input"]
    output_cost = (completion_tokens / 1_000_000) * costs["output"]

    return round(input_cost + output_cost, 8)


def save_pillar_llm_call(
    user: User,
    operation: str,
    response: LLMResponse,
    pillar: Optional[Pillar] = None,
    save_result_data: bool = True,
) -> PillarLLMCall:
    """
    Save LLM call metrics to the database.

    Args:
        user: The user who made the request
        operation: The operation type (e.g., 'validate', 'improve_explained')
        response: The LLMResponse from the orchestrator
        pillar: Optional pillar this call relates to
        save_result_data: Whether to save the full result JSON

    Returns:
        The created PillarLLMCall instance
    """
    metadata = response.metadata
    token_usage = metadata.token_usage

    # Extract token counts
    prompt_tokens = token_usage.prompt_tokens if token_usage else 0
    completion_tokens = token_usage.completion_tokens if token_usage else 0
    total_tokens = token_usage.total_tokens if token_usage else 0

    # Get model name
    model_name = metadata.models_used[0].name if metadata.models_used else "unknown"

    # Calculate cost
    cost_eur = calculate_cost_eur(model_name, prompt_tokens, completion_tokens)

    # Create the record
    llm_call = PillarLLMCall.objects.create(
        user=user,
        pillar=pillar,
        operation=operation,
        model_id=model_name,
        execution_time_ms=metadata.execution_time_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_eur=cost_eur,
        result_data=response.results if save_result_data else None,
    )

    return llm_call
