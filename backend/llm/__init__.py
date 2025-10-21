"""
LLM Orchestrator Package

Unified interface for LLM operations in pix:e.
Provides orchestration, model management, and operation handling.
"""

# Configuration
from llm.config import Config, get_config

# Exceptions
from llm.exceptions import (
    InvalidRequestError,
    ModelUnavailableError,
    OrchestratorError,
    ProviderError,
)

# Handler registry and metadata
from llm.handler_registry import (
    OperationMetadata,
    get_handler,
    get_metadata,
    list_features,
    list_metadata,
    list_operations,
    register_handler,
)

# Handler framework
from llm.operation_handler import BaseOperationHandler

# Core orchestration
from llm.orchestrator import LLMOrchestrator

# Model management
from llm.providers import ModelManager

# Types
from llm.types import (
    LLMRequest,
    LLMResponse,
    ModelDetails,
    ModelInfo,
    ResponseMetadata,
)

__all__ = [
    # Core
    "LLMOrchestrator",
    # Types
    "LLMRequest",
    "LLMResponse",
    "ModelDetails",
    "ModelInfo",
    "ResponseMetadata",
    # Configuration
    "Config",
    "get_config",
    # Exceptions
    "OrchestratorError",
    "ProviderError",
    "ModelUnavailableError",
    "InvalidRequestError",
    # Model management
    "ModelManager",
    # Handler framework
    "BaseOperationHandler",
    "register_handler",
    "get_handler",
    "get_metadata",
    "list_operations",
    "list_metadata",
    "list_features",
    "OperationMetadata",
]
