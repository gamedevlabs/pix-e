"""
Tests for basic orchestrator functionality.

Tests orchestrator initialization, configuration, and basic request validation.
"""

from unittest.mock import Mock

import pytest

from llm import LLMOrchestrator, ProviderError
from llm.config import get_config
from llm.providers import ModelManager
from llm.types import LLMRequest


@pytest.fixture
def orchestrator():
    """Return a configured orchestrator or skip if missing credentials."""
    try:
        return LLMOrchestrator()
    except ProviderError as e:
        pytest.skip(f"Missing provider ({e})")
    except Exception as e:
        raise e


class TestOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_orchestrator_initializes_without_arguments(self, orchestrator):
        """Test that orchestrator can be initialized without arguments."""

        assert orchestrator is not None
        assert orchestrator.model_manager is not None
        assert orchestrator.config is not None

    def test_orchestrator_uses_provided_model_manager(self):
        """Test that orchestrator uses provided ModelManager."""
        mock_manager = Mock(spec=ModelManager)
        orchestrator = LLMOrchestrator(model_manager=mock_manager)

        assert orchestrator.model_manager is mock_manager

    def test_orchestrator_creates_model_manager_if_not_provided(self, orchestrator):
        """Test that orchestrator creates ModelManager if not provided."""

        assert isinstance(orchestrator.model_manager, ModelManager)

    def test_orchestrator_loads_config(self, orchestrator):
        """Test that orchestrator loads configuration."""

        assert orchestrator.config is not None
        # Config should be the same as get_config()
        assert orchestrator.config.default_execution_mode in ["monolithic", "agentic"]


class TestOrchestratorConfiguration:
    """Test orchestrator configuration handling."""

    def test_config_has_default_execution_mode(self):
        """Test that config has default execution mode."""
        config = get_config()

        assert hasattr(config, "default_execution_mode")
        assert config.default_execution_mode in ["monolithic", "agentic"]

    def test_config_has_model_aliases(self):
        """Test that config has model aliases."""
        config = get_config()

        assert hasattr(config, "resolve_model_alias")
        # Test common aliases
        assert config.resolve_model_alias("gemini") == "gemini-2.0-flash-exp"
        assert config.resolve_model_alias("openai") == "gpt-4o-mini"

    def test_config_returns_unknown_alias_as_is(self):
        """Test that unknown aliases are returned as-is."""
        config = get_config()

        unknown_model = "unknown-model-123"
        assert config.resolve_model_alias(unknown_model) == unknown_model


class TestRequestValidation:
    """Test LLMRequest validation."""

    def test_valid_request_creation(self):
        """Test creating a valid LLMRequest."""
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "test", "description": "test description"},
            model_id="gemini-2.0-flash-exp",
        )

        assert request.feature == "pillars"
        assert request.operation == "validate"
        assert request.data == {"name": "test", "description": "test description"}
        assert request.model_id == "gemini-2.0-flash-exp"

    def test_request_with_minimal_fields(self):
        """Test creating request with only required fields."""
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "test", "description": "test"},
        )

        assert request.feature == "pillars"
        assert request.operation == "validate"
        assert request.model_id is None  # Optional field

    def test_request_with_temperature(self):
        """Test creating request with temperature."""
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={},
            temperature=0,
        )

        assert request.temperature == 0

    def test_request_with_max_tokens(self):
        """Test creating request with max_tokens."""
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={},
            max_tokens=1000,
        )

        assert request.max_tokens == 1000

    def test_request_with_mode(self):
        """Test creating request with execution mode."""
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={},
            mode="monolithic",
        )

        assert request.mode == "monolithic"


class TestModelManagerIntegration:
    """Test orchestrator's integration with ModelManager."""

    def test_orchestrator_has_model_manager(self, orchestrator):
        """Test that orchestrator has a model_manager attribute."""

        assert hasattr(orchestrator, "model_manager")
        assert orchestrator.model_manager is not None

    def test_orchestrator_can_access_providers(self, orchestrator):
        """Test that orchestrator can access providers through model_manager."""

        assert hasattr(orchestrator.model_manager, "providers")
        assert isinstance(orchestrator.model_manager.providers, dict)
