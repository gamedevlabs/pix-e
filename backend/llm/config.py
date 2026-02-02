"""
Configuration management for the LLM Orchestrator.

Supports loading configuration from:
- .env files
- Environment variables
- Django settings (when running in Django context)
- Direct initialization (for testing)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, get_args

from llm.types import ExecutionMode, ModelPreference

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed


@dataclass
class Config:
    """
    Configuration for the LLM Orchestrator.

    This class centralizes all configuration options and provides
    sensible defaults while allowing customization via environment
    variables or direct initialization.
    """

    # ============================================
    # Model Provider Configuration
    # ============================================

    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_timeout_seconds: int = 60

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_organization: Optional[str] = None
    openai_timeout_seconds: int = 60

    # Gemini settings
    gemini_api_key: Optional[str] = None
    gemini_timeout_seconds: int = 60

    # ============================================
    # Execution Configuration
    # ============================================

    # Default timeout for operations (milliseconds)
    default_timeout_ms: int = 120000  # 2 minutes

    # Maximum number of agents to run in parallel
    max_parallel_agents: int = 10

    # Default model preference when not specified
    default_model_preference: str = "auto"  # "local" | "cloud" | "auto"

    # Default execution mode when not specified
    default_execution_mode: str = "monolithic"  # "monolithic" | "agentic"

    # Model name aliases: maps friendly names to full model IDs
    model_aliases: dict = field(
        default_factory=lambda: {
            "gemini": "gemini-2.0-flash-exp",
            "openai": "gpt-4o-mini",
        }
    )

    # ============================================
    # Storage Configuration
    # ============================================

    # Path for storing artifacts (prompts, images, etc.)
    artifact_storage_path: Path = field(default_factory=lambda: Path("./artifacts"))

    # Maximum artifact size in bytes (10 MB default)
    max_artifact_size_bytes: int = 10 * 1024 * 1024

    # Artifact cleanup: delete artifacts older than N days
    artifact_retention_days: int = 30

    # ============================================
    # Cache Configuration
    # ============================================

    # Cache time-to-live in seconds
    cache_ttl_seconds: int = 3600  # 1 hour

    # Enable/disable caching
    cache_enabled: bool = True

    # Maximum cache size in MB
    cache_max_size_mb: int = 100

    # ============================================
    # Performance & Limits
    # ============================================

    # Rate limiting: max requests per minute (0 = unlimited)
    rate_limit_per_minute: int = 60

    # Maximum concurrent runs
    max_concurrent_runs: int = 5

    # Request size limit in bytes (1 MB default)
    max_request_size_bytes: int = 1024 * 1024

    # Response size limit in bytes (10 MB default)
    max_response_size_bytes: int = 10 * 1024 * 1024

    # ============================================
    # Feature Flags
    # ============================================

    # Enable streaming support (SSE/WebSocket)
    streaming_enabled: bool = False

    # Enable async execution (background jobs)
    async_execution_enabled: bool = True

    # Enable detailed logging
    debug_logging: bool = False

    # Enable metrics collection
    metrics_enabled: bool = False

    # ============================================
    # Security
    # ============================================

    # Require authentication for API calls
    require_authentication: bool = True

    # Allow CORS (for development)
    allow_cors: bool = False

    # Allowed origins for CORS
    cors_allowed_origins: list = field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # ============================================
    # Class Methods
    # ============================================

    @classmethod
    def from_env(cls) -> "Config":
        """
        Create configuration from environment variables.

        Environment variables follow the pattern:
        LLM_ORCHESTRATOR_<SETTING_NAME>
        Example: LLM_ORCHESTRATOR_OLLAMA_BASE_URL

        For Django integration, checks Django settings first,
        then environment.
        """

        def get_setting(name: str, default=None, cast_type=str):
            """Get setting from Django or environment."""
            # Try Django settings first
            try:
                from django.conf import settings

                # Check if Django is properly configured
                if settings.configured and hasattr(settings, "LLM_ORCHESTRATOR"):
                    django_config = getattr(settings, "LLM_ORCHESTRATOR")
                    django_value = django_config.get(name.upper())
                    if django_value is not None:
                        return django_value
            except (ImportError, Exception):
                pass  # Django not available or not configured

            # Try prefixed environment variable (LLM_ORCHESTRATOR_*)
            env_name = f"LLM_ORCHESTRATOR_{name.upper()}"
            env_value = os.getenv(env_name)

            # If not found, try non-prefixed for common keys
            if env_value is None:
                env_value = os.getenv(name.upper())

            if env_value is None:
                return default

            # Cast to appropriate type
            if cast_type == bool:
                return env_value.lower() in ("true", "1", "yes", "on")
            elif cast_type == int:
                return int(env_value)
            elif cast_type == Path:
                return Path(env_value)
            elif cast_type == list:
                return [s.strip() for s in env_value.split(",")]
            else:
                return env_value

        ollama_url = get_setting("ollama_base_url", "http://localhost:11434")
        openai_key = get_setting("openai_api_key") or os.getenv("OPENAI_API_KEY")
        openai_org = get_setting("openai_organization") or os.getenv(
            "OPENAI_ORGANIZATION"
        )
        gemini_key = get_setting("gemini_api_key") or os.getenv("GEMINI_API_KEY")

        return cls(
            # Model providers
            ollama_base_url=ollama_url,
            ollama_timeout_seconds=get_setting("ollama_timeout_seconds", 30, int),
            openai_api_key=openai_key,
            openai_organization=openai_org,
            openai_timeout_seconds=get_setting("openai_timeout_seconds", 30, int),
            gemini_api_key=gemini_key,
            gemini_timeout_seconds=get_setting("gemini_timeout_seconds", 30, int),
            # Execution
            default_timeout_ms=get_setting("default_timeout_ms", 120000, int),
            max_parallel_agents=get_setting("max_parallel_agents", 10, int),
            default_model_preference=get_setting("default_model_preference", "auto"),
            default_execution_mode=get_setting("default_execution_mode", "monolithic"),
            model_aliases=get_setting(
                "model_aliases",
                {"gemini": "gemini-2.0-flash-exp", "openai": "gpt-4o-mini"},
                dict,
            ),
            # Storage
            artifact_storage_path=get_setting(
                "artifact_storage_path", Path("./artifacts"), Path
            ),
            max_artifact_size_bytes=get_setting(
                "max_artifact_size_bytes", 10 * 1024 * 1024, int
            ),
            artifact_retention_days=get_setting("artifact_retention_days", 30, int),
            # Cache
            cache_ttl_seconds=get_setting("cache_ttl_seconds", 3600, int),
            cache_enabled=get_setting("cache_enabled", True, bool),
            cache_max_size_mb=get_setting("cache_max_size_mb", 100, int),
            # Performance
            rate_limit_per_minute=get_setting("rate_limit_per_minute", 60, int),
            max_concurrent_runs=get_setting("max_concurrent_runs", 5, int),
            max_request_size_bytes=get_setting(
                "max_request_size_bytes", 1024 * 1024, int
            ),
            max_response_size_bytes=get_setting(
                "max_response_size_bytes", 10 * 1024 * 1024, int
            ),
            # Feature flags
            streaming_enabled=get_setting("streaming_enabled", False, bool),
            async_execution_enabled=get_setting("async_execution_enabled", True, bool),
            debug_logging=get_setting("debug_logging", False, bool),
            metrics_enabled=get_setting("metrics_enabled", False, bool),
            # Security
            require_authentication=get_setting("require_authentication", True, bool),
            allow_cors=get_setting("allow_cors", False, bool),
            cors_allowed_origins=get_setting(
                "cors_allowed_origins", ["http://localhost:3000"], list
            ),
        )

    @classmethod
    def from_django_settings(cls) -> "Config":
        """
        Create configuration from Django settings.

        Expects a LLM_ORCHESTRATOR dictionary in Django settings.
        Falls back to environment variables for missing values.
        """
        return cls.from_env()

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.

        Returns:
            List of validation error messages (empty if valid)
        """
        issues = []

        # Check timeouts are positive
        if self.default_timeout_ms <= 0:
            issues.append("default_timeout_ms must be positive")

        if self.ollama_timeout_seconds <= 0:
            issues.append("ollama_timeout_seconds must be positive")

        if self.openai_timeout_seconds <= 0:
            issues.append("openai_timeout_seconds must be positive")

        # Check parallel limits
        if self.max_parallel_agents <= 0:
            issues.append("max_parallel_agents must be positive")

        if self.max_concurrent_runs <= 0:
            issues.append("max_concurrent_runs must be positive")

        # Check size limits
        if self.max_artifact_size_bytes <= 0:
            issues.append("max_artifact_size_bytes must be positive")

        if self.max_request_size_bytes <= 0:
            issues.append("max_request_size_bytes must be positive")

        if self.max_response_size_bytes <= 0:
            issues.append("max_response_size_bytes must be positive")

        # Check cache settings
        if self.cache_ttl_seconds <= 0:
            issues.append("cache_ttl_seconds must be positive")

        if self.cache_max_size_mb <= 0:
            issues.append("cache_max_size_mb must be positive")

        # Check model preference is valid
        valid_preferences = get_args(ModelPreference)
        if self.default_model_preference not in valid_preferences:
            issues.append(
                "default_model_preference must be one of " f"{valid_preferences}"
            )

        # Check execution mode is valid
        valid_modes = get_args(ExecutionMode)
        if self.default_execution_mode not in valid_modes:
            issues.append(f"default_execution_mode must be one of {valid_modes}")

        # Warn if no provider API keys configured
        if not self.openai_api_key and not self.gemini_api_key:
            issues.append(
                "Warning: No cloud provider API keys configured. "
                "Only local models will be available."
            )

        return issues

    def ensure_artifact_directory(self) -> None:
        """
        Ensure artifact storage directory exists.

        Creates the directory if it doesn't exist.
        """
        self.artifact_storage_path.mkdir(parents=True, exist_ok=True)

    def get_provider_config(self, provider: str) -> dict:
        """
        Get configuration for a specific provider.

        Args:
            provider: Provider name ("ollama", "openai", "gemini")

        Returns:
            Dictionary with provider-specific configuration
        """
        if provider == "ollama":
            return {
                "base_url": self.ollama_base_url,
                "timeout_seconds": self.ollama_timeout_seconds,
            }
        elif provider == "openai":
            return {
                "api_key": self.openai_api_key,
                "organization": self.openai_organization,
                "timeout_seconds": self.openai_timeout_seconds,
            }
        elif provider == "gemini":
            return {
                "api_key": self.gemini_api_key,
                "timeout_seconds": self.gemini_timeout_seconds,
            }
        else:
            return {}

    def resolve_model_alias(self, model_name: str) -> str:
        """
        Resolve a model alias to its full model ID.

        Args:
            model_name: Model name or alias
                       (e.g., "gemini" or "gemini-2.0-flash-exp")

        Returns:
            Full model ID (returns input if no alias found)
        """
        return self.model_aliases.get(model_name, model_name)

    def __str__(self) -> str:
        """String representation (hides sensitive data)."""
        openai_display = "***" if self.openai_api_key else "None"
        gemini_display = "***" if self.gemini_api_key else "None"
        return (
            f"Config(\n"
            f"  ollama_base_url={self.ollama_base_url}\n"
            f"  openai_api_key={openai_display}\n"
            f"  gemini_api_key={gemini_display}\n"
            f"  default_timeout_ms={self.default_timeout_ms}\n"
            f"  max_parallel_agents={self.max_parallel_agents}\n"
            f"  cache_enabled={self.cache_enabled}\n"
            f"  async_execution_enabled={self.async_execution_enabled}\n"
            f")"
        )


# ============================================
# Global Default Config
# ============================================

# This is loaded once and can be overridden
_default_config: Optional[Config] = None

def get_model_id(model_name: str) -> str:
    """Map frontend model names to actual model IDs using orchestrator config."""
    config = get_config()
    return config.resolve_model_alias(model_name)

def get_config() -> Config:
    """
    Get the global configuration instance.

    Lazy-loads from environment on first call.
    """
    global _default_config
    if _default_config is None:
        _default_config = Config.from_env()
    return _default_config


def set_config(config: Config) -> None:
    """
    Set the global configuration instance.

    Useful for testing or custom initialization.
    """
    global _default_config
    _default_config = config


def reset_config() -> None:
    """
    Reset configuration to reload from environment.

    Useful for testing.
    """
    global _default_config
    _default_config = None
