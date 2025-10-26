"""
Agent Runtime for Agentic Execution

Provides BaseAgent class for individual agent execution.
Supports both synchronous (execute) and asynchronous (run) execution.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from llm.exceptions import AgentFailureError
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
    temperature: float = 0.3  # Lower for evaluators (more deterministic)

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

            result = model_manager.generate_structured_with_model(
                model_name=model_name,
                prompt=prompt,
                response_schema=self.response_schema,
                temperature=self.temperature,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=result.model_dump() if hasattr(result, "model_dump") else result,
                model_used=model_name,
                execution_time_ms=execution_time_ms,
                error=None,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return self._build_error_result(e, execution_time_ms)

    async def run(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent asynchronously.

        This wraps the synchronous execute() method using asyncio.to_thread()
        to make it non-blocking in async contexts. This is necessary because
        our LLM providers are currently synchronous.

        Args:
            context: Execution context (same as execute())
        """
        # Run synchronous execute() in a thread pool to avoid blocking
        return await asyncio.to_thread(self.execute, context)

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
