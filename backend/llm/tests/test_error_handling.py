"""
Tests for error handling and error responses.

Tests error scenarios, exception handling, and error info structure.
"""

from unittest.mock import Mock

import pytest

from llm import LLMOrchestrator
from llm.exceptions import (
    ModelUnavailableError,
    ProviderError,
    UnknownOperationError,
)
from llm.types import LLMRequest


class TestErrorHandling:
    """Test error handling in orchestrator."""

    def test_unknown_operation_error(self, mock_model_manager):
        """Test handling of unknown operation."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        request = LLMRequest(
            feature="unknown_feature",
            operation="unknown_op",
            data={},
            model_id="gemini-2.0-flash-exp",
        )

        with pytest.raises(UnknownOperationError) as exc_info:
            orchestrator.execute(request)

        # Check error details
        error = exc_info.value
        assert error.code == "UNKNOWN_OPERATION"
        assert "unknown_feature" in str(error).lower()
        assert "unknown_op" in str(error).lower()

    def test_model_unavailable_error(self, mock_model_manager):
        """Test handling of model unavailable error."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        # Mock provider to raise error
        mock_model_manager.generate_structured_with_model.side_effect = (
            ModelUnavailableError(
                model="unavailable-model",
                provider="test-provider",
                reason="Model not found",
            )
        )

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="unavailable-model",
        )

        with pytest.raises(ModelUnavailableError) as exc_info:
            orchestrator.execute(request)

        # Check error details
        error = exc_info.value
        assert error.code == "MODEL_UNAVAILABLE"
        assert "unavailable-model" in str(error)

    def test_provider_error(self, mock_model_manager):
        """Test handling of provider errors."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        # Mock provider to raise error
        mock_model_manager.generate_structured_with_model.side_effect = ProviderError(
            provider="test-provider", message="API error"
        )

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
        )

        with pytest.raises(ProviderError) as exc_info:
            orchestrator.execute(request)

        # Check error details
        error = exc_info.value
        assert error.code == "PROVIDER_ERROR"
        assert "test-provider" in str(error)


class TestErrorInfo:
    """Test error info structure."""

    def test_error_has_code_and_message(self):
        """Test that errors have code and message."""
        error = UnknownOperationError(
            feature="test", operation="invalid", available_operations=[]
        )

        # Should have code and message
        assert hasattr(error, "code")
        assert hasattr(error, "message")
        assert error.code == "UNKNOWN_OPERATION"
        assert error.message != ""

    def test_error_has_context(self):
        """Test that errors have context dict."""
        error = UnknownOperationError(
            feature="test", operation="invalid", available_operations=[]
        )

        # Should have context
        assert hasattr(error, "context")
        assert isinstance(error.context, dict)
        assert "feature" in error.context
        assert "requested_operation" in error.context

    def test_error_can_be_converted_to_dict(self):
        """Test that errors can be converted to dict."""
        error = ModelUnavailableError(
            model="test-model", provider="test-provider", reason="Not available"
        )

        # Should be convertible to dict
        error_dict = error.to_error_info()
        assert isinstance(error_dict, dict)
        assert "code" in error_dict
        assert "message" in error_dict
        assert "severity" in error_dict
        assert "context" in error_dict

    def test_error_severity_is_error(self):
        """Test that error severity is 'error'."""
        error = ProviderError(provider="test", message="Test error")

        error_dict = error.to_error_info()
        assert error_dict["severity"] == "error"


class TestWarningHandling:
    """Test warning handling in responses."""

    def test_warnings_list_exists(self, mock_model_manager):
        """Test that response can contain warnings."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        # Warnings field should exist
        assert hasattr(response, "warnings")

    def test_agent_mode_fallback_creates_warning(self, mock_model_manager):
        """Test that agent mode fallback creates a warning."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
            mode="agentic",  # Request agentic mode
        )

        response = orchestrator.execute(request)

        # Should have warning about fallback
        assert response.warnings is not None
        assert len(response.warnings) > 0

        # Check warning structure
        warning = response.warnings[0]
        assert hasattr(warning, "code")
        assert hasattr(warning, "message")
        assert "not yet implemented" in warning.message.lower()
