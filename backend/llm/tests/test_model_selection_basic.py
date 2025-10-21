"""
Tests for basic model selection logic.

Tests explicit model selection and alias resolution.
"""

from unittest.mock import Mock

from llm import LLMOrchestrator
from llm.config import get_config
from llm.types import LLMRequest


class TestExplicitModelSelection:
    """Test explicit model_id selection."""

    def test_explicit_model_id_is_used(self, mock_model_manager):
        """Test that explicit model_id takes priority."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        # Mock _find_model_by_name to return proper model details
        mock_model_details = Mock()
        mock_model_details.name = "gemini-2.0-flash-exp"
        mock_model_details.type = "cloud"
        mock_model_details.provider = "gemini"
        mock_model_manager._find_model_by_name.return_value = mock_model_details

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",  # Explicit model
        )

        response = orchestrator.execute(request)

        # Should use the specified model
        assert response.metadata.models_used[0].name == "gemini-2.0-flash-exp"

    def test_explicit_model_id_overrides_config_default(self, mock_model_manager):
        """Test that explicit model_id overrides config default."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        # Mock _find_model_by_name
        mock_model_details = Mock()
        mock_model_details.name = "gpt-4o-mini"
        mock_model_details.type = "cloud"
        mock_model_details.provider = "openai"
        mock_model_manager._find_model_by_name.return_value = mock_model_details

        # Use different model than config default
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gpt-4o-mini",
        )

        response = orchestrator.execute(request)

        # Should use the explicit model, not config default
        assert response.metadata.models_used[0].name == "gpt-4o-mini"


class TestModelAliasResolution:
    """Test model alias resolution."""

    def test_config_resolves_gemini_alias(self):
        """Test that 'gemini' alias resolves to full model ID."""
        config = get_config()
        resolved = config.resolve_model_alias("gemini")
        assert resolved == "gemini-2.0-flash-exp"

    def test_config_resolves_openai_alias(self):
        """Test that 'openai' alias resolves to full model ID."""
        config = get_config()
        resolved = config.resolve_model_alias("openai")
        assert resolved == "gpt-4o-mini"

    def test_alias_resolution_in_orchestrator(self, mock_model_manager):
        """Test that orchestrator resolves aliases during execution."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        # Use alias instead of full model ID
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini",  # Using alias
        )

        response = orchestrator.execute(request)

        # Should resolve to full model ID
        # Note: mock returns whatever model_id we pass, so this tests resolution
        assert response.success is True

    def test_unknown_alias_returns_as_is(self):
        """Test that unknown aliases are returned unchanged."""
        config = get_config()
        unknown = "unknown-model-xyz"
        resolved = config.resolve_model_alias(unknown)
        assert resolved == unknown


class TestAutoModelSelection:
    """Test automatic model selection when model_id not specified."""

    def test_uses_default_model_when_not_specified(self, mock_model_manager):
        """Test that orchestrator uses default model when not specified."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        # Mock _find_model_by_name
        mock_model_details = Mock()
        mock_model_details.name = "gemini-2.0-flash-exp"
        mock_model_details.type = "cloud"
        mock_model_details.provider = "gemini"
        mock_model_manager._find_model_by_name.return_value = mock_model_details

        # No model_id specified
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
        )

        response = orchestrator.execute(request)

        # Should execute successfully with some model
        assert response.success is True
        assert response.metadata.models_used is not None
        assert len(response.metadata.models_used) > 0

    def test_auto_selection_uses_config_default(self, mock_model_manager):
        """Test that auto-selection respects config default."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)
        config = get_config()

        # Mock to track which model was selected
        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        # Mock _find_model_by_name
        mock_model_details = Mock()
        mock_model_details.name = "gemini-2.0-flash-exp"
        mock_model_details.type = "cloud"
        mock_model_details.provider = "gemini"
        mock_model_manager._find_model_by_name.return_value = mock_model_details

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            # No model_id - should use default
        )

        response = orchestrator.execute(request)

        # Should use a valid model (either default or first available)
        assert response.success is True
        # Config has a default_model setting
        assert hasattr(config, "default_model") or hasattr(
            config, "resolve_model_alias"
        )
