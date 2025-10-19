"""
LLM Orchestrator Package

A unified, model-agnostic interface for all LLM interactions in pix:e.
Supports both monolithic and agentic execution modes.

"""

__version__ = "0.1.0"

# Auto-import operations to register handlers
import importlib as _importlib

# Configuration exports
from llm_orchestrator.config import (
    Config,
    get_config,
    reset_config,
    set_config,
)

# Exception exports
from llm_orchestrator.exceptions import (  # Base; Request validation; Auth; Resources; Rate limiting; Model/Provider; Timeout; Warnings; Helpers  # noqa: E501
    AgentFailureError,
    AuthenticationError,
    CacheError,
    IdempotencyConflictError,
    InsufficientResourcesError,
    InvalidRequestError,
    ModelUnavailableError,
    OrchestratorError,
    PartialSuccessError,
    PermissionDeniedError,
    ProviderError,
    RateLimitError,
    RunNotFoundError,
    TimeoutError,
    UnknownFeatureError,
    UnknownOperationError,
    ValidationError,
    get_http_status_for_error,
)

# Feature and operation registry exports
from llm_orchestrator.features import (  # Feature IDs; Operation IDs; Metadata; Convenience functions  # noqa: E501
    FeatureID,
    MoodboardsOperations,
    OperationMetadata,
    OperationRegistry,
    PillarsOperations,
    SPARCOperations,
    get_operation,
    list_features,
    list_operations,
)

# Type exports
from llm_orchestrator.types import (  # Request/Response; Metadata; Models; Job/Run; Inventory; Enums  # noqa: E501
    AgentInfo,
    CachePolicy,
    ErrorInfo,
    ExecutionMode,
    LLMRequest,
    LLMResponse,
    ModelInfo,
    ModelInventory,
    ModelPreference,
    OperationCatalog,
    ResponseMetadata,
    RunInfo,
    RunStatus,
    TokenUsage,
    WarningInfo,
)

# Auto-import operations to register handlers
_importlib.import_module("llm_orchestrator.operations")

# Core orchestrator
from llm_orchestrator.core import LLMOrchestrator  # noqa: E402

__all__ = [
    # Main orchestrator
    "LLMOrchestrator",
    # Main types
    "LLMRequest",
    "LLMResponse",
    "ResponseMetadata",
    "ErrorInfo",
    "WarningInfo",
    "ModelInfo",
    "AgentInfo",
    "TokenUsage",
    "RunInfo",
    "RunStatus",
    "ModelInventory",
    "OperationCatalog",
    "ExecutionMode",
    "ModelPreference",
    "CachePolicy",
    # Exceptions
    "OrchestratorError",
    "InvalidRequestError",
    "ValidationError",
    "UnknownFeatureError",
    "UnknownOperationError",
    "AuthenticationError",
    "PermissionDeniedError",
    "RunNotFoundError",
    "IdempotencyConflictError",
    "RateLimitError",
    "ModelUnavailableError",
    "ProviderError",
    "AgentFailureError",
    "InsufficientResourcesError",
    "TimeoutError",
    "CacheError",
    "PartialSuccessError",
    "get_http_status_for_error",
    # Configuration
    "Config",
    "get_config",
    "set_config",
    "reset_config",
    # Features & Operations
    "FeatureID",
    "PillarsOperations",
    "SPARCOperations",
    "MoodboardsOperations",
    "OperationMetadata",
    "OperationRegistry",
    "get_operation",
    "list_features",
    "list_operations",
]
