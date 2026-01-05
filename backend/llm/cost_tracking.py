"""
Shared cost tracking utilities for LLM operations.

Provides centralized model pricing and cost calculation for all features.
"""

from decimal import Decimal
from typing import Dict

# Model pricing per 1M tokens (EUR)
# Updated prices should be maintained in this single location
MODEL_COSTS: Dict[str, Dict[str, float]] = {
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.25, "output": 9.00},
    "gpt-4-turbo": {"input": 9.00, "output": 27.00},
    "gpt-5.2": {"input": 1.75, "output": 14.00},
}


def calculate_cost_eur(
    model_name: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> Decimal:
    """
    Calculate cost in EUR based on token usage.

    Args:
        model_name: The model identifier (e.g., "gpt-4o-mini", "gemini-2.0-flash-exp")
        prompt_tokens: Number of input tokens used
        completion_tokens: Number of output tokens generated

    Returns:
        Estimated cost in EUR with 8 decimal precision

    Examples:
        >>> calculate_cost_eur("gpt-4o-mini", 1000, 500)
        Decimal('0.00040500')

        >>> calculate_cost_eur("gemini-2.0-flash-exp", 10000, 5000)
        Decimal('0.00000000')
    """
    costs = MODEL_COSTS.get(model_name, {"input": 0.0, "output": 0.0})

    input_cost = Decimal(str((prompt_tokens / 1_000_000) * costs["input"]))
    output_cost = Decimal(str((completion_tokens / 1_000_000) * costs["output"]))

    total_cost = input_cost + output_cost
    return total_cost.quantize(Decimal("0.00000001"))
