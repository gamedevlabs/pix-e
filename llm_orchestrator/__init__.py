"""
LLM Orchestrator Package

A unified, model-agnostic interface for all LLM interactions in pix:e.
Supports both monolithic and agentic execution modes.

"""

__version__ = "0.1.0"

# Type exports
from llm_orchestrator.types import (
    # Request/Response
    LLMRequest,
    LLMResponse,
    # Metadata
    ResponseMetadata,
    ErrorInfo,
    WarningInfo,
    # Models
    ModelInfo,
    AgentInfo,
    TokenUsage,
    # Job/Run
    RunInfo,
    RunStatus,
    # Inventory
    ModelInventory,
    OperationCatalog,
    # Enums
    ExecutionMode,
    ModelPreference,
    CachePolicy,
)

# Exception exports
from llm_orchestrator.exceptions import (
    # Base
    OrchestratorError,
    # Request validation
    InvalidRequestError,
    ValidationError,
    UnknownFeatureError,
    UnknownOperationError,
    # Auth
    AuthenticationError,
    PermissionDeniedError,
    # Resources
    RunNotFoundError,
    IdempotencyConflictError,
    # Rate limiting
    RateLimitError,
    # Model/Provider
    ModelUnavailableError,
    ProviderError,
    AgentFailureError,
    InsufficientResourcesError,
    # Timeout
    TimeoutError,
    # Warnings
    CacheError,
    PartialSuccessError,
    # Helpers
    get_http_status_for_error,
)

__all__ = [
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
]

