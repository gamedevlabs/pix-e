"""
Response builder utilities for LLM orchestrator.

Provides helper functions to build LLMResponse objects from
handler and agent execution results.
"""

from typing import Any, List, Set

from llm.events import EventCollector
from llm.providers.base import StructuredResult
from llm.providers.manager import ModelManager
from llm.types import (
    AgentInfo,
    ExecutionResult,
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ResponseMetadata,
    TokenUsage,
)


def build_handler_response(
    request: LLMRequest,
    result: Any,
    model_name: str,
    mode: str,
    execution_time_ms: int,
    model_manager: ModelManager,
) -> LLMResponse:
    """
    Build LLMResponse from handler execution result.

    Args:
        request: Original LLM request
        result: Handler execution result
        model_name: Name of model used
        mode: Execution mode (monolithic/agentic)
        execution_time_ms: Total execution time in milliseconds
        model_manager: ModelManager for looking up model details
    """
    # Extract token usage if result is StructuredResult
    token_usage = None
    actual_result = result

    if isinstance(result, StructuredResult):
        token_usage = TokenUsage(
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
        )
        actual_result = result.data

    # Get model info
    try:
        model_details = model_manager._find_model_by_name(model_name)
        model_info = ModelInfo(
            name=model_details.name,
            type=model_details.type,
            provider=model_details.provider,
        )
    except Exception:
        # Fallback if model lookup fails
        model_info = ModelInfo(name=model_name, type="cloud", provider="unknown")

    # Build metadata
    metadata = ResponseMetadata(
        execution_time_ms=execution_time_ms,
        mode=mode,  # type: ignore
        models_used=[model_info],
        token_usage=token_usage,
    )

    return LLMResponse(
        success=True,
        results=(
            actual_result.model_dump()
            if hasattr(actual_result, "model_dump")
            else actual_result
        ),
        metadata=metadata,
    )


def build_agent_response(
    request: LLMRequest,
    execution_result: ExecutionResult,
    event_collector: EventCollector,
    model_manager: ModelManager,
) -> LLMResponse:
    """
    Build LLMResponse from agent execution result.

    Args:
        request: Original LLM request
        execution_result: ExecutionResult from agent workflow
        event_collector: EventCollector with execution timeline
        model_manager: ModelManager for looking up model details
    """
    # Extract models used and aggregate token usage from agent results
    models_used_names: Set[str] = set()
    agents_used: List[AgentInfo] = []
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    for agent_result in execution_result.agent_results:
        if agent_result.model_used:
            models_used_names.add(agent_result.model_used)

        # Aggregate token usage
        total_prompt_tokens += agent_result.prompt_tokens
        total_completion_tokens += agent_result.completion_tokens
        total_tokens += agent_result.total_tokens

        # Build AgentInfo
        agents_used.append(
            AgentInfo(
                name=agent_result.agent_name,
                execution_time_ms=agent_result.execution_time_ms,
                model=agent_result.model_used or "unknown",
                prompt_tokens=agent_result.prompt_tokens,
                completion_tokens=agent_result.completion_tokens,
                total_tokens=agent_result.total_tokens,
            )
        )

    # Get model info for each unique model
    models_used: List[ModelInfo] = []
    for model_name in models_used_names:
        try:
            model_details = model_manager._find_model_by_name(model_name)
            models_used.append(
                ModelInfo(
                    name=model_details.name,
                    type=model_details.type,
                    provider=model_details.provider,
                )
            )
        except Exception:
            models_used.append(
                ModelInfo(name=model_name, type="cloud", provider="unknown")
            )

    # Build token usage if any tokens were used
    token_usage = None
    if total_tokens > 0:
        token_usage = TokenUsage(
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
        )

    # Build metadata
    metadata = ResponseMetadata(
        execution_time_ms=execution_result.total_execution_time_ms,
        mode="agentic",  # type: ignore
        models_used=models_used,
        agents_used=agents_used,
        events=event_collector.get_events(),
        token_usage=token_usage,
    )

    return LLMResponse(
        success=execution_result.success,
        results=execution_result.aggregated_data,
        metadata=metadata,
        errors=execution_result.errors or [],
        warnings=execution_result.warnings if execution_result.warnings else None,
    )
