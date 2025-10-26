"""
Type definitions for the LLM Orchestrator.

This module contains all Pydantic models that define the API contract.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================
# Enums and Literals
# ============================================

ExecutionMode = Literal["monolithic", "agentic"]
ModelPreference = Literal["local", "cloud", "auto"]
CachePolicy = Literal["use", "bypass", "refresh"]
RoutingPolicy = Literal["auto", "local_first", "cloud_first"]
ProviderType = Literal["local", "cloud"]
ErrorSeverity = Literal["error", "warning"]
RunStatus = Literal["pending", "running", "completed", "failed"]
ArtifactType = Literal["prompt", "intermediate_json", "image", "text", "file"]


# ============================================
# Request Models
# ============================================


class SamplingConfig(BaseModel):
    """Sampling controls for LLM generation."""

    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    seed: Optional[int] = Field(None, description="Enable repeatability in evaluations")


class CapabilityRequirements(BaseModel):
    """Capability hints for model routing."""

    vision: Optional[bool] = None
    multimodal: Optional[bool] = None
    function_calling: Optional[bool] = None
    json_strict: Optional[bool] = None
    min_context_window: Optional[int] = Field(
        None, description="Minimum tokens required"
    )


class RoutingConfig(BaseModel):
    """Routing policy configuration."""

    policy: Optional[RoutingPolicy] = "auto"
    fallbacks: Optional[bool] = Field(True, description="Allow provider/model fallback")


class UserContext(BaseModel):
    """User context for request."""

    user_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    api_tokens: Optional[Dict[str, str]] = Field(
        None,
        description="User-specific API tokens (orchestrator may ignore)",
    )


class RequestMetadata(BaseModel):
    """Optional metadata for request."""

    request_id: Optional[str] = None
    timeout_ms: Optional[int] = Field(None, gt=0)
    cache_policy: Optional[CachePolicy] = "use"
    api_version: Optional[str] = "1.0"
    ab_test: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = Field(
        None, description="For safe retries and deduplication"
    )


class LLMRequest(BaseModel):
    """
    Unified request format for all LLM operations.

    This is the main request type that features send to the orchestrator.

    Recommended usage (plain strings):
        LLMRequest(feature="pillars", operation="validate", ...)

    Available operations can be discovered dynamically. Example:
        from backend.llm import list_operations
        ops = list_operations(feature="pillars")
        # ['pillars.validate', 'pillars.improve', ...]
    """

    # Feature identification (accepts enums or strings)
    feature: str = Field(
        ...,
        description="Feature name (e.g., 'pillars', 'sparc', 'moodboards')",
    )
    operation: str = Field(
        ...,
        description=(
            "Feature-specific operation name " "(e.g., 'validate', 'evaluate_concept')"
        ),
    )

    # Operation payload
    data: Dict[str, Any] = Field(..., description="Operation-specific data")

    # Execution configuration (optional with defaults from config)
    mode: Optional[ExecutionMode] = Field(
        None,
        description=(
            "Execution mode (e.g., 'monolithic', 'agentic'). " "Defaults to config."
        ),
    )
    model_preference: Optional[ModelPreference] = Field(
        None, description="Model selection preference. Defaults to config."
    )

    # Model specification (convenience fields - can also use route config)
    model_id: Optional[str] = Field(
        None, description="Explicit model to use (overrides preference)"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, description="Maximum tokens to generate"
    )
    provider_options: Optional[Dict[str, Any]] = Field(
        None, description="Provider-specific options"
    )

    # Optional configurations (structured alternative to convenience)
    capabilities: Optional[CapabilityRequirements] = None
    sampling: Optional[SamplingConfig] = None
    route: Optional[RoutingConfig] = None

    # Context
    user_context: Optional[UserContext] = None

    # Metadata
    metadata: Optional[RequestMetadata] = None

    # Ensure enums are coerced to their string values
    @field_validator("feature", "operation", mode="before")
    @classmethod
    def _coerce_enum_to_str(cls, v: Any) -> Any:
        try:
            # Support Enum-like objects
            return v.value if hasattr(v, "value") else v
        except Exception:
            return v


# ============================================
# Response Models
# ============================================


class ModelInfo(BaseModel):
    """Information about a model used in execution."""

    name: str = Field(
        ..., description="Model name (e.g., 'llama3.1:8b', 'gpt-4o-mini')"
    )
    type: ProviderType = Field(..., description="Model type")
    provider: str = Field(..., description="Provider name (e.g., 'ollama', 'openai')")


class AgentInfo(BaseModel):
    """Information about an agent's execution."""

    name: str = Field(..., description="Agent name")
    execution_time_ms: int = Field(..., ge=0)
    model: str = Field(..., description="Model name used by this agent")


class TokenUsage(BaseModel):
    """Token usage statistics."""

    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)
    total_tokens: int = Field(..., ge=0)


class ArtifactInfo(BaseModel):
    """Information about an artifact created during execution."""

    id: str = Field(..., description="Unique artifact ID")
    type: ArtifactType
    uri: Optional[str] = Field(
        None,
        description="Storage URI (e.g., 'store://runs/{run_id}/{artifact}')",
    )
    bytes_size: Optional[int] = Field(None, ge=0)
    sha256: Optional[str] = None
    created_by_agent: Optional[str] = None


class RoutingDecision(BaseModel):
    """Information about a routing decision made."""

    reason: str = Field(..., description="Why this decision was made")
    from_: Optional[str] = Field(None, alias="from", description="Original value")
    to: Optional[str] = Field(None, description="Selected value")


class ResolvedSampling(BaseModel):
    """Resolved sampling configuration actually used."""

    temperature: float
    top_p: float
    max_tokens: Optional[int] = None
    seed: Optional[int] = None


class ResponseMetadata(BaseModel):
    """Execution metadata returned with response."""

    request_id: Optional[str] = None
    execution_time_ms: int = Field(..., ge=0)
    mode: ExecutionMode

    # Model information
    models_used: List[ModelInfo] = Field(default_factory=list)

    # Agent information (agentic mode only)
    agents_used: Optional[List[AgentInfo]] = None

    # Performance info
    parallel_execution: Optional[bool] = None
    cache_hit: Optional[bool] = None
    token_usage: Optional[TokenUsage] = None

    # Schema & versioning
    operation_schema: Optional[str] = Field(
        None,
        description=("Operation schema used (e.g., 'sparc.evaluate_concept@1.0.0')"),
    )
    api_version: Optional[str] = None

    # Resolved execution details
    resolved_sampling: Optional[ResolvedSampling] = None
    routing_decisions: Optional[List[RoutingDecision]] = None

    # Artifacts/provenance
    artifacts: Optional[List[ArtifactInfo]] = None

    # Event timeline (agentic mode only)
    events: Optional[List["StreamEvent"]] = None


class ErrorInfo(BaseModel):
    """Error information."""

    code: str = Field(..., description="Error code (e.g., 'MODEL_UNAVAILABLE')")
    message: str = Field(..., description="Human-readable error message")
    severity: ErrorSeverity
    context: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional diagnostic info (trace_id, suggested_fixes)",
    )


class WarningInfo(BaseModel):
    """Warning information (non-fatal issues)."""

    code: str = Field(..., description="Warning code")
    message: str = Field(..., description="Human-readable warning message")
    context: Optional[Dict[str, Any]] = None


class LLMResponse(BaseModel):
    """
    Unified response format for all LLM operations.

    This is returned by the orchestrator after execution.
    """

    success: bool = Field(..., description="Whether the operation succeeded")
    results: Dict[str, Any] = Field(..., description="Operation-specific results")
    metadata: ResponseMetadata
    errors: List[ErrorInfo] = Field(default_factory=list)
    warnings: Optional[List[WarningInfo]] = None


# ============================================
# Job/Run Models
# ============================================


class RunInfo(BaseModel):
    """
    Information about a queued/running job.

    Returned when wait=False.
    """

    run_id: str = Field(..., description="Unique run identifier")
    status: RunStatus
    created_at: str = Field(..., description="ISO 8601 timestamp")
    feature: str
    operation: str


# ============================================
# Model Inventory Models
# ============================================


class ModelCapabilities(BaseModel):
    """Capabilities of a model."""

    json_strict: Optional[bool] = None
    vision: Optional[bool] = None
    multimodal: Optional[bool] = None
    function_calling: Optional[bool] = None
    min_context_window: Optional[int] = None


class ModelDetails(BaseModel):
    """Detailed information about an available model."""

    name: str
    provider: str
    type: ProviderType
    capabilities: ModelCapabilities


class ModelInventory(BaseModel):
    """List of available models with capabilities."""

    models: List[ModelDetails] = Field(default_factory=list)


# ============================================
# Operation Registry Models
# ============================================


class OperationInfo(BaseModel):
    """Information about a registered operation."""

    id: str = Field(..., description="Operation ID (e.g., 'pillars.validate')")
    version: str = Field(..., description="Semantic version")
    request_schema_uri: str = Field(..., description="URI to request JSON schema")
    response_schema_uri: str = Field(..., description="URI to response JSON schema")


class OperationCatalog(BaseModel):
    """Catalog of supported operations."""

    operations: List[OperationInfo] = Field(default_factory=list)


# ============================================
# Agent Task Models
# ============================================


class AgentTask(BaseModel):
    """
    A task for an agent to execute.

    Used by the router and executor to coordinate agent execution.
    """

    agent_name: str = Field(..., description="Name of the agent to execute")
    priority: int = Field(..., ge=0, description="Execution priority (lower = earlier)")
    depends_on: List[str] = Field(
        default_factory=list, description="Other agent names this depends on"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )


# ============================================
# Execution Result Models
# ============================================


class AgentResult(BaseModel):
    """Result from a single agent execution."""

    agent_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[ErrorInfo] = None
    execution_time_ms: int = Field(..., ge=0)
    model_used: Optional[str] = None


class ExecutionResult(BaseModel):
    """Aggregated result from executing multiple agents."""

    success: bool
    agent_results: List[AgentResult] = Field(default_factory=list)
    aggregated_data: Dict[str, Any] = Field(default_factory=dict)
    total_execution_time_ms: int = Field(..., ge=0)
    errors: List[ErrorInfo] = Field(default_factory=list)
    warnings: List[WarningInfo] = Field(default_factory=list)


# ============================================
# Cost Estimation Models
# ============================================


class CostEstimate(BaseModel):
    """Estimated cost for an operation."""

    estimated_tokens: int = Field(..., ge=0)
    estimated_time_ms: int = Field(..., ge=0)
    estimated_cost_usd: Optional[float] = Field(None, ge=0.0)


# ============================================
# Event Stream Models (for future SSE/WebSocket support)
# ============================================


class StreamEvent(BaseModel):
    """Base class for stream events."""

    event_type: str
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    run_id: str


class RunStartedEvent(StreamEvent):
    """Event emitted when a run starts."""

    event_type: Literal["run_started"] = "run_started"
    received_at: str


class ModelRoutedEvent(StreamEvent):
    """Event emitted when a model is selected."""

    event_type: Literal["model_routed"] = "model_routed"
    from_: Optional[str] = Field(None, alias="from")
    to: ModelInfo
    reason: str


class AgentStartedEvent(StreamEvent):
    """Event emitted when an agent starts."""

    event_type: Literal["agent_started"] = "agent_started"
    name: str


class AgentOutputEvent(StreamEvent):
    """Event emitted when an agent produces output."""

    event_type: Literal["agent_output"] = "agent_output"
    name: str
    chunk: Optional[str] = Field(None, description="Optional streaming text")


class ArtifactCreatedEvent(StreamEvent):
    """Event emitted when an artifact is created."""

    event_type: Literal["artifact_created"] = "artifact_created"
    artifact: ArtifactInfo


class RunCompletedEvent(StreamEvent):
    """Event emitted when a run completes."""

    event_type: Literal["run_completed"] = "run_completed"
    success: bool


class ErrorEvent(StreamEvent):
    """Event emitted when an error occurs."""

    event_type: Literal["error"] = "error"
    error: ErrorInfo


class WarningEvent(StreamEvent):
    """Event emitted when a warning occurs."""

    event_type: Literal["warning"] = "warning"
    warning: WarningInfo
