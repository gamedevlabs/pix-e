"""
Main LLM Orchestrator.

The orchestrator is the primary entry point for all LLM operations.
It routes requests to either operation handlers (monolithic mode) or
agents (agentic mode).

Supports per-user API keys via for_user() and for_user_and_key() factory methods.
"""

import time
from typing import Any, Optional, cast

from llm.config import get_config
from llm.exceptions import (
    InvalidRequestError,
    OrchestratorError,
    ProviderError,
    UnknownOperationError,
)
from llm.handler_registry import get_handler
from llm.providers import ModelManager
from llm.types import (
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ResponseMetadata,
    WarningInfo,
)


class LLMOrchestrator:
    """
    Main orchestrator for LLM operations.

    Supports two execution modes:
    1. Handler Mode (monolithic): Direct execution via operation handlers
    2. Agent Mode (agentic): Multi-agent orchestration (future)

    Also supports per-user API keys:
    - LLMOrchestrator()  — uses global env-var config (legacy)
    - LLMOrchestrator.for_user(user)  — uses ALL user's active API keys
    - LLMOrchestrator.for_user_and_key(user, api_key_id)  — uses ONE specific key
    """

    def __init__(self, model_manager: Optional[ModelManager] = None):
        """
        Initialize the orchestrator.

        Args:
            model_manager: Optional ModelManager instance. If not provided,
                          a new one will be created from env config.
        """
        self.model_manager = model_manager or ModelManager()
        self.config = get_config()

    @classmethod
    def for_user(cls, user, enc_key: bytes) -> "LLMOrchestrator":
        """
        Create an orchestrator that uses ALL of the user's active API keys.

        The encryption key is obtained from the user's Django session via
        ``accounts.encryption.get_encryption_key_from_session``.  If the key
        is missing (user not logged in), a ``RuntimeError`` is raised.

        Unlike the global orchestrator (which reads API keys from environment
        variables), a per-user orchestrator loads keys from
        ``accounts.models.UserApiKey`` and creates a dedicated provider
        instance for each active key.  Ollama is still sourced from env
        config as a fallback.

        Args:
            user: The Django user whose API keys should be used.
            enc_key: The Fernet encryption key bytes from the user's
                session.  Retrieved via
                ``accounts.encryption.get_encryption_key_from_session``.

        Returns:
            A new ``LLMOrchestrator`` instance backed by the user's keys.

        Raises:
            RuntimeError: If ``enc_key`` is ``None`` or empty (user not
                authenticated).
        """
        if not enc_key:
            raise RuntimeError(
                "No encryption key in session. "
                "User must log in to access API keys."
            )
        orch = cls.__new__(cls)
        orch.config = get_config()
        orch.model_manager = ModelManager.for_user(user, enc_key)
        return orch

    @classmethod
    def for_user_and_key(
        cls, user, api_key_id: str, enc_key: bytes
    ) -> "LLMOrchestrator":
        """
        Create an orchestrator scoped to a SINGLE specific user API key.

        Like ``for_user()``, this requires a session-derived encryption key.
        The resulting orchestrator only has access to the one provider
        corresponding to the given key (plus Ollama if available).

        Args:
            user: The Django user who owns the API key.
            api_key_id: The primary key of the ``UserApiKey`` record.
            enc_key: The Fernet encryption key bytes from the user's
                session.

        Returns:
            A new ``LLMOrchestrator`` instance backed by exactly one
            user API key.

        Raises:
            RuntimeError: If ``enc_key`` is ``None`` or empty.
            django.http.Http404: If the ``UserApiKey`` does not exist or
                does not belong to the given user.
        """
        if not enc_key:
            raise RuntimeError(
                "No encryption key in session. "
                "User must log in to access API keys."
            )
        orch = cls.__new__(cls)
        orch.config = get_config()
        orch.model_manager = ModelManager.for_user_and_key(user, api_key_id, enc_key)
        return orch

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
            if isinstance(e, OrchestratorError):
                raise

            raise ProviderError(
                message=f"Handler execution failed: {str(e)}", provider="handler"
            )

    def _execute_agent_mode(self, request: LLMRequest) -> LLMResponse:
        """
        Execute request using agent orchestration (agentic mode).

        For now, this is a placeholder that falls back to handler mode.
        """
        response = self._execute_handler_mode(request)

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
        try:
            resolved = self.model_manager._find_model_by_name(model_name)
            model_details = resolved[0]
            model_info = ModelInfo(
                name=model_details.name,
                type=model_details.type,
                provider=model_details.provider,
            )
        except Exception:
            model_info = ModelInfo(name=model_name, type="cloud", provider="unknown")

        metadata = ResponseMetadata(
            execution_time_ms=execution_time_ms,
            mode=mode,
            models_used=[model_info],
        )

        return LLMResponse(
            success=True,
            results=result.model_dump() if hasattr(result, "model_dump") else result,
            metadata=metadata,
        )
