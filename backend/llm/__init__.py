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

# Features
from llm.features import (
    FeatureID,
    MoodboardsOperations,
    PillarsOperations,
    SPARCOperations,
    get_operation,
    list_features,
)
from llm.handler_registry import get_handler, list_operations, register_handler

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
    "list_operations",
    # Features
    "FeatureID",
    "PillarsOperations",
    "SPARCOperations",
    "MoodboardsOperations",
    "get_operation",
    "list_features",
]
