"""
Agent Runtime for Agentic Execution

Provides BaseAgent class for individual agent execution.
This is the synchronous version - async wrapper will be added in the next step.
"""

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

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent synchronously.

        This is the main execution method that:
        1. Validates input
        2. Builds prompt
        3. Selects appropriate model
        4. Calls LLM
        5. Validates response
        6. Returns AgentResult

        Args:
            context: Execution context with keys:
                - model_manager: ModelManager instance
                - data: Operation input data
        """
        start_time = time.time()

        # Extract context
        model_manager: ModelManager = context["model_manager"]
        data: Dict[str, Any] = context.get("data", {})

        try:
            self.validate_input(data)

            prompt = self.build_prompt(data)

            # Select model based on capability requirements
            if self.capability_requirements:
                model = model_manager.auto_select_model(
                    requirements=self.capability_requirements,
                    model_preference=context.get("model_preference", "auto"),
                )
                model_name = model.name
            else:
                # Use first available model
                models = model_manager.list_available_models()
                if not models:
                    raise AgentFailureError(
                        agent_name=self.name,
                        message="No models available",
                        context={
                            "capability_requirements": self.capability_requirements
                        },
                    )
                model_name = models[0].name

            # Execute LLM call with structured output
            result = model_manager.generate_structured_with_model(
                model_name=model_name,
                prompt=prompt,
                response_schema=self.response_schema,
                temperature=self.temperature,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Return successful result
            return AgentResult(
                agent_name=self.name,
                success=True,
                data=result.model_dump() if hasattr(result, "model_dump") else result,
                model_used=model_name,
                execution_time_ms=execution_time_ms,
                error=None,
            )

        except ValidationError as e:
            # Pydantic validation failed
            execution_time_ms = int((time.time() - start_time) * 1000)
            return AgentResult(
                agent_name=self.name,
                success=False,
                data=None,
                model_used=None,
                execution_time_ms=execution_time_ms,
                error=ErrorInfo(
                    code="VALIDATION_ERROR",
                    message=f"Response validation failed: {str(e)}",
                    severity="error",
                    context={"validation_errors": e.errors()},
                    diagnostics=None,
                ),
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)

            if isinstance(e, AgentFailureError):
                error_info = ErrorInfo(
                    code="AGENT_FAILURE",
                    message=e.message,
                    severity="error",
                    context=e.context,
                    diagnostics=None,
                )
            else:
                error_info = ErrorInfo(
                    code="EXECUTION_ERROR",
                    message=error_msg,
                    severity="error",
                    context={"agent": self.name, "exception_type": type(e).__name__},
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