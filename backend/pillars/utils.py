"""
Utility functions for pillar operations.

Includes LLM call tracking and cost calculation.
"""

from typing import Any, Dict, List, Optional, Tuple

from django.contrib.auth.models import User

from llm.cost_tracking import calculate_cost_eur
from llm.types import AgentResult, ExecutionResult, LLMResponse

from .models import Pillar, PillarLLMCall


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


# Mapping from agent names to operation choices
AGENT_NAME_TO_OPERATION = {
    "concept_fit": "concept_fit",
    "contradictions": "contradictions",
    "suggest_additions": "suggest_additions_agent",
    "contradiction_resolution": "contradiction_resolution",
}


def save_agent_result_llm_call(
    user: User,
    operation: str,
    result: AgentResult,
    input_data: Optional[Dict[str, Any]] = None,
    pillar: Optional[Pillar] = None,
    parent_call: Optional[PillarLLMCall] = None,
    save_result_data: bool = True,
) -> PillarLLMCall:
    """
    Save LLM call metrics from an AgentResult.

    Args:
        user: The user who made the request
        operation: The operation type
        result: The AgentResult from agent execution
        input_data: Optional input data to save
        pillar: Optional pillar this call relates to
        parent_call: Optional parent call (for agent sub-calls)
        save_result_data: Whether to save the full result JSON

    Returns:
        The created PillarLLMCall instance
    """
    model_name = result.model_used or "unknown"
    cost_eur = calculate_cost_eur(
        model_name, result.prompt_tokens, result.completion_tokens
    )

    llm_call = PillarLLMCall.objects.create(
        user=user,
        pillar=pillar,
        parent_call=parent_call,
        operation=operation,
        model_id=model_name,
        execution_time_ms=result.execution_time_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        total_tokens=result.total_tokens,
        estimated_cost_eur=cost_eur,
        input_data=input_data,
        result_data=result.data if save_result_data else None,
    )

    return llm_call


def save_execution_result_llm_calls(
    user: User,
    result: ExecutionResult,
    input_data: Optional[Dict[str, Any]] = None,
    save_result_data: bool = True,
) -> Tuple[PillarLLMCall, List[PillarLLMCall]]:
    """
    Save LLM call metrics from an ExecutionResult (evaluate_all).

    Creates:
    1. One aggregated parent record with total tokens/cost/time
    2. One record per agent, linked to the parent

    Args:
        user: The user who made the request
        result: The ExecutionResult from graph execution
        input_data: Optional input data to save
        save_result_data: Whether to save result data

    Returns:
        Tuple of (parent_call, list of agent_calls)
    """
    # Calculate aggregated metrics
    total_prompt_tokens = sum(r.prompt_tokens for r in result.agent_results)
    total_completion_tokens = sum(r.completion_tokens for r in result.agent_results)
    total_tokens = sum(r.total_tokens for r in result.agent_results)

    # Get unique models used
    models_used = list(set(r.model_used for r in result.agent_results if r.model_used))
    model_name = models_used[0] if models_used else "unknown"

    # Calculate total cost
    total_cost = sum(
        calculate_cost_eur(
            r.model_used or "unknown", r.prompt_tokens, r.completion_tokens
        )
        for r in result.agent_results
    )

    # Create the aggregated parent record
    parent_call = PillarLLMCall.objects.create(
        user=user,
        pillar=None,
        parent_call=None,
        operation="evaluate_all",
        model_id=model_name,
        execution_time_ms=result.total_execution_time_ms,
        prompt_tokens=total_prompt_tokens,
        completion_tokens=total_completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_eur=total_cost,
        input_data=input_data,
        result_data=result.aggregated_data if save_result_data else None,
    )

    # Create individual agent records linked to parent
    agent_calls = []
    for agent_result in result.agent_results:
        operation = AGENT_NAME_TO_OPERATION.get(
            agent_result.agent_name, agent_result.agent_name
        )
        agent_call = save_agent_result_llm_call(
            user=user,
            operation=operation,
            result=agent_result,
            input_data=input_data,
            parent_call=parent_call,
            save_result_data=save_result_data,
        )
        agent_calls.append(agent_call)

    return parent_call, agent_calls
