"""
Operation Handler Framework

Handlers execute feature operations without agents. They provide:
- Prompt building from input data
- Response schema definition
- Execution logic using ModelManager
- Metadata for discovery and documentation
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

from llm.providers.manager import ModelManager
from llm.types import CapabilityRequirements


class BaseOperationHandler(ABC):
    """
    Abstract base class for operation handlers.

    Handlers are lightweight executors that:
    1. Build prompts from input data
    2. Define response schemas
    3. Execute via ModelManager
    4. Return validated responses
    5. Provide metadata for discovery
    """

    # Subclasses MUST define these
    operation_id: str = ""  # e.g., "pillars.validate"
    response_schema: Type[BaseModel]  # Pydantic model for response

    # Optional metadata (with defaults)
    description: str = ""
    version: str = "1.0.0"
    capability_requirements: Optional[CapabilityRequirements] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        Auto-register handler when class is defined.

        This metaclass hook is called whenever a subclass is created.
        """
        super().__init_subclass__(**kwargs)

        # Only register if operation_id is defined (not the base class)
        if hasattr(cls, "operation_id") and cls.operation_id:
            from llm.handler_registry import register_handler

            register_handler(cls.operation_id, cls)

    def __init__(self, model_manager: ModelManager) -> None:
        """
        Initialize handler with model manager.
        """
        self.model_manager = model_manager

    @abstractmethod
    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the LLM prompt from input data.
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data before execution.
        """
        # Default: no validation
        # Subclasses can override
        pass

    @property
    def feature_id(self) -> str:
        """Extract feature ID from operation_id."""
        return self.operation_id.split(".")[0] if "." in self.operation_id else ""

    @property
    def operation_name(self) -> str:
        """Extract operation name from operation_id."""
        return (
            self.operation_id.split(".")[1]
            if "." in self.operation_id
            else self.operation_id
        )

    def execute(
        self,
        data: Dict[str, Any],
        model_name: str,
        temperature: float = 0,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> BaseModel:
        """
        Execute the operation.
        """
        # Validate input
        self.validate_input(data)

        # Build prompt
        prompt = self.build_prompt(data)

        # Execute with model manager
        result = self.model_manager.generate_structured_with_model(
            model_name=model_name,
            prompt=prompt,
            response_schema=self.response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return result

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(operation_id={self.operation_id})"
