"""
Operation Handler Framework

Handlers execute feature operations without agents. They provide:
- Prompt building from input data
- Response schema definition
- Execution logic using ModelManager
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from llm_orchestrator.models.manager import ModelManager
from llm_orchestrator.types import CapabilityRequirements


class BaseOperationHandler(ABC):
    """
    Abstract base class for operation handlers.
    
    Handlers are lightweight executors that:
    1. Build prompts from input data
    2. Define response schemas
    3. Execute via ModelManager
    4. Return validated responses
    """
    
    # Subclasses must define these
    operation_id: str  # e.g., "pillars.validate"
    response_schema: Type[BaseModel]  # Pydantic model for response
    capability_requirements: Optional[CapabilityRequirements] = None
    
    def __init__(self, model_manager: ModelManager):
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
    
    def execute(
        self,
        data: Dict[str, Any],
        model_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
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
            **kwargs
        )
        
        return result
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(operation_id={self.operation_id})"