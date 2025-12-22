"""
Agent Runtime for Agentic Execution

Provides BaseAgent class for individual agent execution.
Supports both synchronous (execute) and asynchronous (run) execution.
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from llm.exceptions import AgentFailureError
from llm.logfire_config import get_logfire
from llm.providers.base import StructuredResult
from llm.providers.manager import ModelManager
from llm.types import AgentResult, CapabilityRequirements, ErrorInfo


class BaseAgent(ABC):
    """
    Base class for individual agents.

    Each agent represents a specialized task that:
    1. Builds a prompt from input data
    2. Calls an LLM via ModelManager
    3. Returns validated results

    Subclasses must implement:
    - name: Agent identifier
    - response_schema: Pydantic model for response validation
    - build_prompt(): Construct the LLM prompt
    """

    name: str = ""
    response_schema: Type[BaseModel]  # Pydantic model for response

    capability_requirements: Optional[CapabilityRequirements] = None
    temperature: float = 0

    def __init__(self) -> None:
        """Initialize agent."""
        if not self.name:
            raise ValueError(
                f"{self.__class__.__name__} must define 'name' class attribute"
            )
        if not hasattr(self, "response_schema"):
            raise ValueError(
                f"{self.__class__.__name__} must define 'response_schema' "
                "class attribute"
            )

    @abstractmethod
    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the LLM prompt from input data.

        Args:
            data: Operation-specific input data
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data before execution.

        Override this method to add custom validation logic.

        Args:
            data: Operation-specific input data
        """
        pass

    def _select_model(
        self, model_manager: ModelManager, context: Dict[str, Any]
    ) -> str:
        """Select appropriate model based on capability requirements."""
        # If explicit model_id is provided, use it
        if "model_id" in context and context["model_id"]:
            return context["model_id"]

        # Otherwise use auto-selection based on capabilities
        if self.capability_requirements:
            model = model_manager.auto_select_model(
                requirements=self.capability_requirements,
                model_preference=context.get("model_preference", "auto"),
            )
            return model.name
        else:
            models = model_manager.list_available_models()
            if not models:
                raise AgentFailureError(
                    agent_name=self.name,
                    message="No models available",
                    context={"capability_requirements": self.capability_requirements},
                )
            return models[0].name

    def _build_error_result(
        self, error: Exception, execution_time_ms: int
    ) -> AgentResult:
        """Build AgentResult for error cases."""
        if isinstance(error, ValidationError):
            error_info = ErrorInfo(
                code="VALIDATION_ERROR",
                message=f"Response validation failed: {str(error)}",
                severity="error",
                context={"validation_errors": error.errors()},
                diagnostics=None,
            )
        elif isinstance(error, AgentFailureError):
            error_info = ErrorInfo(
                code="AGENT_FAILURE",
                message=error.message,
                severity="error",
                context=error.context,
                diagnostics=None,
            )
        else:
            error_info = ErrorInfo(
                code="EXECUTION_ERROR",
                message=str(error),
                severity="error",
                context={"agent": self.name, "exception_type": type(error).__name__},
                diagnostics=None,
            )

        return AgentResult(
            agent_name=self.name,
            success=False,
            data=None,
            model_used=None,
            execution_time_ms=execution_time_ms,
            error=error_info,
        )

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent synchronously.

        Args:
            context: Execution context with keys:
                - model_manager: ModelManager instance
                - data: Operation input data
        """
        start_time = time.time()
        model_manager: ModelManager = context["model_manager"]
        data: Dict[str, Any] = context.get("data", {})

        try:
            self.validate_input(data)
            prompt = self.build_prompt(data)
            model_name = self._select_model(model_manager, context)

            # Create a custom span with agent name to wrap the LLM call
            logfire = get_logfire()
            with logfire.span(
                f"{self.name}",
                agent_name=self.name,
                model=model_name,
            ):
                result = model_manager.generate_structured_with_model(
                    model_name=model_name,
                    prompt=prompt,
                    response_schema=self.response_schema,
                    temperature=self.temperature,
                )

            # Extract token usage if result is StructuredResult
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            actual_result = result

            if isinstance(result, StructuredResult):
                prompt_tokens = result.prompt_tokens
                completion_tokens = result.completion_tokens
                total_tokens = result.total_tokens
                actual_result = result.data

            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=(
                    actual_result.model_dump()
                    if hasattr(actual_result, "model_dump")
                    else actual_result
                ),
                model_used=model_name,
                execution_time_ms=execution_time_ms,
                error=None,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return self._build_error_result(e, execution_time_ms)

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent asynchronously using native async providers.

        Uses async LLM provider methods for true parallel execution.

        Args:
            context: Execution context (same as execute())
        """
        start_time = time.time()
        model_manager: ModelManager = context["model_manager"]
        data: Dict[str, Any] = context.get("data", {})

        try:
            self.validate_input(data)
            prompt = self.build_prompt(data)
            model_name = self._select_model(model_manager, context)

            # Create a custom span with agent name to wrap the LLM call
            logfire = get_logfire()
            with logfire.span(
                f"{self.name}",
                agent_name=self.name,
                model=model_name,
            ):
                # Use async method for true parallel execution
                result = await model_manager.generate_structured_with_model_async(
                    model_name=model_name,
                    prompt=prompt,
                    response_schema=self.response_schema,
                    temperature=self.temperature,
                )

            # Extract token usage if result is StructuredResult
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0
            actual_result = result

            if isinstance(result, StructuredResult):
                prompt_tokens = result.prompt_tokens
                completion_tokens = result.completion_tokens
                total_tokens = result.total_tokens
                actual_result = result.data

            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=(
                    actual_result.model_dump()
                    if hasattr(actual_result, "model_dump")
                    else actual_result
                ),
                model_used=model_name,
                execution_time_ms=execution_time_ms,
                error=None,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        except Exception as e:
            import logging
            import traceback

            logger = logging.getLogger(__name__)
            error_type = type(e).__name__
            logger.error(
                f"[AGENT_ERROR] {self.name} async run failed: "
                f"{error_type}: {str(e)}\nTraceback:\n{traceback.format_exc()}"
            )
            execution_time_ms = int((time.time() - start_time) * 1000)
            return self._build_error_result(e, execution_time_ms)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name={self.name})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"{self.__class__.__name__}("
            f"name={self.name}, "
            f"capabilities={self.capability_requirements})"
        )
