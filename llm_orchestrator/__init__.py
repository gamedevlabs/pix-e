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
]

