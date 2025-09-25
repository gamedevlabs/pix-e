"""
Base LLM Service Interface
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for LLM services"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> bool:
        """Load the model into memory"""

    @abstractmethod
    def unload_model(self) -> bool:
        """Unload the model from memory"""

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs: Any) -> Any:
        """Generate text based on prompt"""

    @abstractmethod
    def get_suggestions(self, prompt: str, **kwargs: Any) -> List[str]:
        """Generate multiple text suggestions"""

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""


class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""
