"""
Main LLM Orchestrator.

The orchestrator is the primary entry point for all LLM operations.
It routes requests to either operation handlers (monolithic mode) or
agents (agentic mode).
"""

import asyncio
import time
from typing import Optional, cast

from llm.agent_registry import get_graph, has_graph
from llm.config import get_config
from llm.events import EventCollector
from llm.exceptions import (
    InvalidRequestError,
    OrchestratorError,
    ProviderError,
    UnknownOperationError,
)
from llm.handler_registry import get_handler
from llm.providers import ModelManager
from llm.response_builder import build_agent_response, build_handler_response
from llm.types import LLMRequest, LLMResponse, WarningInfo


class LLMOrchestrator:
    """
    Main orchestrator for LLM operations.

    Routes requests to handlers (monolithic) or agents (agentic),
    manages model selection, and tracks execution metadata.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        """Initialize orchestrator with optional ModelManager."""
        self.model_manager = model_manager or ModelManager()
        self.config = get_config()

    def execute(self, request: LLMRequest) -> LLMResponse:
        """Execute LLM operation in monolithic or agentic mode."""
        # Determine execution mode
        mode = request.mode or self.config.default_execution_mode

        if mode == "monolithic":
            return self._execute_handler_mode(request)
        elif mode == "agentic":
            return self._execute_agent_mode(request)
        else:
            raise InvalidRequestError(
                message=f"Unknown execution mode: {mode}",
                context={"mode": mode, "valid_modes": ["monolithic", "agentic"]},
            )

    def _execute_handler_mode(self, request: LLMRequest) -> LLMResponse:
        """Execute request using operation handlers (monolithic mode)."""
        start_time = time.time()
        operation_id = f"{request.feature}.{request.operation}"

        try:
            handler_class = get_handler(operation_id)
        except UnknownOperationError:
            raise

        handler = handler_class(self.model_manager)
        model_name = self._select_model(request, handler)

        try:
            result = handler.execute(
                data=request.data,
                model_name=model_name,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                **(request.provider_options or {}),
            )

            execution_time_ms = int((time.time() - start_time) * 1000)
            return build_handler_response(
                request=request,
                result=result,
                model_name=model_name,
                mode="monolithic",
                execution_time_ms=execution_time_ms,
                model_manager=self.model_manager,
            )

        except Exception as e:
            if isinstance(e, OrchestratorError):
                raise
            raise ProviderError(
                message=f"Handler execution failed: {str(e)}", provider="handler"
            )

    def _execute_agent_mode(self, request: LLMRequest) -> LLMResponse:
        """Execute request using agent orchestration (agentic mode)."""
        operation_id = f"{request.feature}.{request.operation}"

        if not has_graph(operation_id):
            response = self._execute_handler_mode(request)
            response.warnings = response.warnings or []
            response.warnings.append(
                WarningInfo(
                    code="AGENT_GRAPH_NOT_FOUND",
                    message=f"No agent graph for {operation_id}, using handler mode",
                    context={"operation_id": operation_id},
                )
            )
            return response

        graph_class = get_graph(operation_id)
        event_collector = EventCollector()
        graph = graph_class(self.model_manager, self.config, event_collector)

        try:
            execution_result = asyncio.run(graph.run(request))
        except Exception as e:
            raise OrchestratorError(
                message=f"Agent graph execution failed: {str(e)}",
                code="AGENT_EXECUTION_FAILED",
                context={"operation_id": operation_id, "error": str(e)},
            )

        return build_agent_response(
            request=request,
            execution_result=execution_result,
            event_collector=event_collector,
            model_manager=self.model_manager,
        )

    def _select_model(self, request: LLMRequest, handler) -> str:
        """Select model: explicit > auto-select > first available."""
        if request.model_id:
            return request.model_id

        if (
            hasattr(handler, "capability_requirements")
            and handler.capability_requirements
        ):
            try:
                from llm.types import ModelPreference

                preference = (
                    request.model_preference or self.config.default_model_preference
                )
                model = self.model_manager.auto_select_model(
                    requirements=handler.capability_requirements,
                    model_preference=cast(ModelPreference, preference),
                )
                return model.name
            except Exception:
                pass

        models = self.model_manager.list_available_models()
        if models:
            return models[0].name

        from llm.exceptions import ModelUnavailableError

        raise ModelUnavailableError(
            model="auto-select", provider="any", reason="No models available"
        )
