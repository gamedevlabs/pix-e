"""
Custom exceptions for the LLM Orchestrator.

These exceptions map to the error codes defined in the API specification
and provide structured error handling throughout the orchestrator.
"""

from typing import Any, Dict, Optional


class OrchestratorError(Exception):
    """
    Base exception for all orchestrator errors.
    
    All custom exceptions inherit from this to allow catching all
    orchestrator-specific errors.
    """

    def __init__(
        self,
        message: str,
        code: str,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}
        self.suggestion = suggestion

    def to_error_info(self) -> Dict[str, Any]:
        """Convert to ErrorInfo dict for API responses."""
        error_info = {
            "code": self.code,
            "message": self.message,
            "severity": "error",
            "context": self.context,
        }
        
        if self.suggestion:
            error_info["context"]["suggestion"] = self.suggestion
        
        return error_info


# ============================================
# Request Validation Errors (400)
# ============================================


class InvalidRequestError(OrchestratorError):
    """
    Request format is invalid.
    
    HTTP Status: 400
    Error Code: INVALID_REQUEST
    
    Raised when:
    - Malformed JSON
    - Missing required fields
    - Invalid field types
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="INVALID_REQUEST",
            context=context,
            suggestion=suggestion or "Check request format against API specification",
        )


class ValidationError(OrchestratorError):
    """
    Input data validation failed.
    
    HTTP Status: 400
    Error Code: VALIDATION_ERROR
    
    Raised when:
    - Data doesn't match operation schema
    - Constraints violated (e.g., negative timeout)
    - Invalid enum values
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        suggestion: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            context=context,
            suggestion=suggestion or "Verify input data against operation schema",
        )


class UnknownFeatureError(OrchestratorError):
    """
    Feature not recognized.
    
    HTTP Status: 400
    Error Code: UNKNOWN_FEATURE
    
    Raised when:
    - Feature name typo
    - Feature not implemented
    """

    def __init__(
        self,
        feature: str,
        available_features: Optional[list] = None,
    ):
        context = {"requested_feature": feature}
        if available_features:
            context["available_features"] = available_features
        
        super().__init__(
            message=f"Unknown feature: '{feature}'",
            code="UNKNOWN_FEATURE",
            context=context,
            suggestion=f"Available features: {', '.join(available_features)}" if available_features else None,
        )


class UnknownOperationError(OrchestratorError):
    """
    Operation not recognized for this feature.
    
    HTTP Status: 400
    Error Code: UNKNOWN_OPERATION
    
    Raised when:
    - Operation name typo
    - Operation not implemented for this feature
    """

    def __init__(
        self,
        feature: str,
        operation: str,
        available_operations: Optional[list] = None,
    ):
        context = {
            "feature": feature,
            "requested_operation": operation,
        }
        if available_operations:
            context["available_operations"] = available_operations
        
        super().__init__(
            message=f"Unknown operation '{operation}' for feature '{feature}'",
            code="UNKNOWN_OPERATION",
            context=context,
            suggestion=f"Available operations: {', '.join(available_operations)}" if available_operations else None,
        )


# ============================================
# Authentication & Authorization Errors (401, 403)
# ============================================


class AuthenticationError(OrchestratorError):
    """
    Authentication failed.
    
    HTTP Status: 401
    Error Code: AUTH_ERROR
    
    Raised when:
    - Missing credentials
    - Invalid API key
    - Expired token
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            context=context,
            suggestion="Check API credentials and ensure they are valid",
        )


class PermissionDeniedError(OrchestratorError):
    """
    User lacks permission for this operation.
    
    HTTP Status: 403
    Error Code: PERMISSION_DENIED
    
    Raised when:
    - User not allowed for provider/model
    - Quota exceeded
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="PERMISSION_DENIED",
            context=context,
        )


# ============================================
# Resource Errors (404, 409)
# ============================================


class RunNotFoundError(OrchestratorError):
    """
    Run ID not found.
    
    HTTP Status: 404
    Error Code: RUN_NOT_FOUND
    
    Raised when:
    - Invalid run_id
    - Run expired/deleted
    """

    def __init__(self, run_id: str):
        super().__init__(
            message=f"Run not found: {run_id}",
            code="RUN_NOT_FOUND",
            context={"run_id": run_id},
            suggestion="Check that the run_id is correct and the run hasn't expired",
        )


class IdempotencyConflictError(OrchestratorError):
    """
    Idempotency key conflict.
    
    HTTP Status: 409
    Error Code: IDEMPOTENCY_CONFLICT
    
    Raised when:
    - Same idempotency_key used with different payload
    """

    def __init__(
        self,
        idempotency_key: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"Idempotency conflict for key: {idempotency_key}",
            code="IDEMPOTENCY_CONFLICT",
            context=context or {"idempotency_key": idempotency_key},
            suggestion="Use a new idempotency_key or retry with the same payload",
        )


# ============================================
# Rate Limiting Errors (429)
# ============================================


class RateLimitError(OrchestratorError):
    """
    Rate limit exceeded.
    
    HTTP Status: 429
    Error Code: RATE_LIMIT
    
    Raised when:
    - Too many requests to cloud API
    - User quota exceeded
    """

    def __init__(
        self,
        message: str,
        retry_after_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        if retry_after_seconds:
            ctx["retry_after_seconds"] = retry_after_seconds
        
        super().__init__(
            message=message,
            code="RATE_LIMIT",
            context=ctx,
            suggestion=f"Wait {retry_after_seconds} seconds before retrying" if retry_after_seconds else "Wait before retrying",
        )


# ============================================
# Model/Provider Errors (500, 502, 503)
# ============================================


class ModelUnavailableError(OrchestratorError):
    """
    Requested model not available.
    
    HTTP Status: 503
    Error Code: MODEL_UNAVAILABLE
    
    Raised when:
    - Ollama not running
    - Model not pulled
    - Invalid API key
    - Provider down
    """

    def __init__(
        self,
        model: str,
        provider: str,
        reason: Optional[str] = None,
        suggestion: Optional[str] = None,
    ):
        message = f"Model '{model}' from provider '{provider}' is not available"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message=message,
            code="MODEL_UNAVAILABLE",
            context={
                "requested_model": model,
                "provider": provider,
                "reason": reason,
            },
            suggestion=suggestion or self._get_default_suggestion(provider, model),
        )
    
    def _get_default_suggestion(self, provider: str, model: str) -> str:
        """Provide provider-specific suggestions."""
        if provider == "ollama":
            return f"Ensure Ollama is running and run 'ollama pull {model}'"
        elif provider == "openai":
            return "Check your OpenAI API key is valid"
        else:
            return f"Check that {provider} is configured correctly"


class ProviderError(OrchestratorError):
    """
    Upstream provider error.
    
    HTTP Status: 502
    Error Code: PROVIDER_ERROR
    
    Raised when:
    - Provider returns error
    - Network issues
    - Invalid response from provider
    """

    def __init__(
        self,
        provider: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        ctx["provider"] = provider
        
        super().__init__(
            message=f"Provider '{provider}' error: {message}",
            code="PROVIDER_ERROR",
            context=ctx,
        )


class AgentFailureError(OrchestratorError):
    """
    Agent execution failed.
    
    HTTP Status: 500
    Error Code: AGENT_FAILURE
    
    Raised when:
    - Agent crashed
    - Unexpected output
    - Internal error
    """

    def __init__(
        self,
        agent_name: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        ctx["agent"] = agent_name
        
        super().__init__(
            message=f"Agent '{agent_name}' failed: {message}",
            code="AGENT_FAILURE",
            context=ctx,
        )


class InsufficientResourcesError(OrchestratorError):
    """
    Not enough compute resources.
    
    HTTP Status: 503
    Error Code: INSUFFICIENT_RESOURCES
    
    Raised when:
    - GPU memory full
    - CPU overloaded
    - Disk space full
    """

    def __init__(
        self,
        resource_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        ctx["resource_type"] = resource_type
        
        super().__init__(
            message=f"Insufficient {resource_type}: {message}",
            code="INSUFFICIENT_RESOURCES",
            context=ctx,
            suggestion="Free up resources or use a smaller model",
        )


# ============================================
# Timeout Errors (504)
# ============================================


class TimeoutError(OrchestratorError):
    """
    Operation exceeded timeout.
    
    HTTP Status: 504
    Error Code: TIMEOUT
    
    Raised when:
    - Model too slow
    - Network timeout
    - Operation deadlock
    """

    def __init__(
        self,
        operation: str,
        timeout_ms: int,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        ctx["operation"] = operation
        ctx["timeout_ms"] = timeout_ms
        
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_ms}ms",
            code="TIMEOUT",
            context=ctx,
            suggestion="Increase timeout or use a faster model",
        )


# ============================================
# Warning-level Errors (non-fatal)
# ============================================


class CacheError(OrchestratorError):
    """
    Cache operation failed (non-critical).
    
    Error Code: CACHE_ERROR
    Severity: warning
    
    This is a warning, not a fatal error.
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            context=context,
        )

    def to_error_info(self) -> Dict[str, Any]:
        """Override to set severity as warning."""
        error_info = super().to_error_info()
        error_info["severity"] = "warning"
        return error_info


class PartialSuccessError(OrchestratorError):
    """
    Some agents succeeded, some failed.
    
    Error Code: PARTIAL_SUCCESS
    Severity: warning
    
    This is a warning - operation partially succeeded.
    """

    def __init__(
        self,
        message: str,
        succeeded: list,
        failed: list,
        context: Optional[Dict[str, Any]] = None,
    ):
        ctx = context or {}
        ctx["succeeded"] = succeeded
        ctx["failed"] = failed
        
        super().__init__(
            message=message,
            code="PARTIAL_SUCCESS",
            context=ctx,
        )

    def to_error_info(self) -> Dict[str, Any]:
        """Override to set severity as warning."""
        error_info = super().to_error_info()
        error_info["severity"] = "warning"
        return error_info


# ============================================
# Helper Functions
# ============================================


def get_http_status_for_error(error: OrchestratorError) -> int:
    """
    Map error code to HTTP status code.
    
    Based on the HTTP Status Mapping table in the API specification.
    """
    status_map = {
        "INVALID_REQUEST": 400,
        "VALIDATION_ERROR": 400,
        "UNKNOWN_FEATURE": 400,
        "UNKNOWN_OPERATION": 400,
        "AUTH_ERROR": 401,
        "PERMISSION_DENIED": 403,
        "RUN_NOT_FOUND": 404,
        "IDEMPOTENCY_CONFLICT": 409,
        "RATE_LIMIT": 429,
        "AGENT_FAILURE": 500,
        "PROVIDER_ERROR": 502,
        "MODEL_UNAVAILABLE": 503,
        "INSUFFICIENT_RESOURCES": 503,
        "TIMEOUT": 504,
        "CACHE_ERROR": 200,  # Warning, not an error
        "PARTIAL_SUCCESS": 200,  # Warning, not an error
    }
    
    return status_map.get(error.code, 500)

