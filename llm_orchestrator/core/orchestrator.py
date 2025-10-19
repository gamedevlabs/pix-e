"""
Main LLM Orchestrator.

The orchestrator is the primary entry point for all LLM operations.
It routes requests to either operation handlers (monolithic mode) or
agents (agentic mode).
"""

import time
from typing import Any, Optional, cast

from llm_orchestrator.config import get_config
from llm_orchestrator.core.handler_registry import get_handler
from llm_orchestrator.exceptions import (
    InvalidRequestError,
    UnknownOperationError,
)
from llm_orchestrator.models import ModelManager
from llm_orchestrator.types import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ResponseMetadata,
)


class LLMOrchestrator:
    """
    Main orchestrator for LLM operations.

    Supports two execution modes:
    1. Handler Mode (monolithic): Direct execution via operation handlers
    2. Agent Mode (agentic): Multi-agent orchestration (future)

    The orchestrator:
    - Routes requests to appropriate handlers/agents
    - Manages model selection
    - Tracks execution metadata
    - Handles errors uniformly
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        """
        Initialize the orchestrator.

        Args:
            model_manager: Optional ModelManager instance. If not provided,
                          a new one will be created.
        """
        self.model_manager = model_manager or ModelManager()
        self.config = get_config()

    def execute(self, request: LLMRequest) -> LLMResponse:
        """
        Execute an LLM operation.

        Routes the request to the appropriate execution path based on mode:
        - "monolithic": Direct handler execution
        - "agentic": Agent-based execution (future)
        """
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
        """
        Execute request using operation handlers (monolithic mode).

        This is the direct execution path for current pix:e features.
        """
        start_time = time.time()

        # Build operation ID
        operation_id = f"{request.feature}.{request.operation}"

        # Get handler
        try:
            handler_class = get_handler(operation_id)
        except UnknownOperationError:
            raise

        # Instantiate handler with model manager
        handler = handler_class(self.model_manager)

        # Determine model to use
        model_name = self._select_model(request, handler)

        # Execute handler
        try:
            result = handler.execute(
                data=request.data,
                model_name=model_name,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                **(request.provider_options or {}),
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Build response
            return self._build_response(
                request=request,
                result=result,
                model_name=model_name,
                mode="monolithic",
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            # Re-raise orchestrator exceptions as-is
            from llm_orchestrator.exceptions import OrchestratorError

            if isinstance(e, OrchestratorError):
                raise

            # Wrap other exceptions
            from llm_orchestrator.exceptions import ProviderError

            raise ProviderError(
                message=f"Handler execution failed: {str(e)}", provider="handler"
            )

    def _execute_agent_mode(self, request: LLMRequest) -> LLMResponse:
        """
        Execute request using agent orchestration (agentic mode).

        For now, this is a placeholder that falls back to handler mode.
        """
        # TODO: Implement agent-based execution
        # For now, fall back to handler mode with a warning
        from llm_orchestrator.types import WarningInfo

        # Execute via handlers
        response = self._execute_handler_mode(request)

        # Add warning about fallback
        response.warnings = response.warnings or []
        response.warnings.append(
            WarningInfo(
                code="AGENT_MODE_NOT_IMPLEMENTED",
                message="Agent mode not yet implemented, falling back to handler mode",
                context={"feature": request.feature, "operation": request.operation},
            )
        )

        return response

    def _select_model(self, request: LLMRequest, handler) -> str:
        """
        Select which model to use for the request.

        Priority:
        1. Explicit model_id in request
        2. Automatic selection based on handler requirements
        3. First available model (fallback)
        """
        # If user specified a model, use it directly
        if request.model_id:
            return request.model_id

        # Try automatic selection based on handler requirements
        if (
            hasattr(handler, "capability_requirements")
            and handler.capability_requirements
        ):
            try:
                from llm_orchestrator.types import ModelPreference

                preference = (
                    request.model_preference or self.config.default_model_preference
                )
                model = self.model_manager.auto_select_model(
                    requirements=handler.capability_requirements,
                    model_preference=cast(ModelPreference, preference),
                )
                return model.name
            except Exception:
                # Fall through to simple fallback
                pass

        # Simple fallback: use first available model
        models = self.model_manager.list_available_models()
        if models:
            return models[0].name

        # No models available
        from llm_orchestrator.exceptions import ModelUnavailableError

        raise ModelUnavailableError(
            model="auto-select", provider="any", reason="No models available"
        )

    def _build_response(
        self,
        request: LLMRequest,
        result: Any,
        model_name: str,
        mode: str,
        execution_time_ms: int,
    ) -> LLMResponse:
        """
        Build LLMResponse from handler result.
        """
        # Get model info
        try:
            model_details = self.model_manager._find_model_by_name(model_name)
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
        )

        return LLMResponse(
            success=True,
            results=result.model_dump() if hasattr(result, "model_dump") else result,
            metadata=metadata,
        )
