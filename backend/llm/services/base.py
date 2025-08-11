"""
Base LLM Service Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    """Abstract base class for LLM services"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.is_loaded = False

    @abstractmethod
    def load_model(self) -> bool:
        """Load the model into memory"""
        pass

    @abstractmethod
    def unload_model(self) -> bool:
        """Unload the model from memory"""
        pass

    @abstractmethod
    def generate_text(self, prompt: str, max_length: int = 100, **kwargs) -> str:
        """Generate text based on prompt"""
        pass

    @abstractmethod
    def get_suggestions(
        self, prompt: str, num_suggestions: int = 3, **kwargs
    ) -> List[str]:
        """Generate multiple text suggestions"""
        pass

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass


class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""

    pass
