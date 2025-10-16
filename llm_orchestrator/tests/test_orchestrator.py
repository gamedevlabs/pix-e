"""
Tests for LLM Orchestrator core functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock
from llm_orchestrator import LLMOrchestrator, LLMRequest
from llm_orchestrator.exceptions import (
    InvalidRequestError,
    UnknownOperationError,
)
from llm_orchestrator.types import LLMResponse


class TestOrchestratorBasics:
    """Test basic orchestrator functionality."""

    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        orchestrator = LLMOrchestrator()
        assert orchestrator is not None
        assert orchestrator.model_manager is not None
        assert orchestrator.config is not None

    def test_invalid_execution_mode(self):
        """Test that invalid execution mode raises error."""
        orchestrator = LLMOrchestrator()
        # We can't pass invalid mode due to Pydantic validation
        # This tests the orchestrator's internal validation
        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "test", "description": "test"},
            mode="monolithic"
        )
        # Manually override to test internal validation
        request.mode = "invalid_mode"

        with pytest.raises(InvalidRequestError) as exc_info:
            orchestrator.execute(request)

        assert "Unknown execution mode" in str(exc_info.value)
        assert exc_info.value.context["mode"] == "invalid_mode"

    def test_unknown_operation(self):
        """Test that unknown operation raises error."""
        orchestrator = LLMOrchestrator()
        request = LLMRequest(
            feature="unknown_feature",
            operation="unknown_operation",
            data={},
            model_id="gemini"
        )

        with pytest.raises(UnknownOperationError):
            orchestrator.execute(request)

    def test_execution_time_tracked(self):
        """Test that execution time is tracked in metadata."""
        orchestrator = LLMOrchestrator()

        # Mock the handler to avoid actual LLM calls
        mock_handler_class = Mock()
        mock_handler = MagicMock()
        mock_handler.execute.return_value = {"is_valid": True, "issues": [], "suggestions": []}
        mock_handler_class.return_value = mock_handler

        # Patch the handler registry
        from llm_orchestrator.core import handler_registry
        original_get_handler = handler_registry.get_handler
        handler_registry.get_handler = Mock(return_value=mock_handler_class)

        try:
            request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": "test", "description": "test"},
                model_id="gemini"
            )

            response = orchestrator.execute(request)

            assert isinstance(response, LLMResponse)
            assert response.metadata.execution_time_ms > 0
            assert response.success is True
        finally:
            # Restore original handler
            handler_registry.get_handler = original_get_handler


class TestModelSelection:
    """Test model selection logic."""

    def test_explicit_model_id_used(self):
        """Test that explicit model_id is used when provided."""
        orchestrator = LLMOrchestrator()

        # Mock handler
        mock_handler_class = Mock()
        mock_handler = MagicMock()
        mock_handler.execute.return_value = {"result": "success"}
        mock_handler_class.return_value = mock_handler

        from llm_orchestrator.core import handler_registry
        original_get_handler = handler_registry.get_handler
        handler_registry.get_handler = Mock(return_value=mock_handler_class)

        try:
            request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": "test", "description": "test"},
                model_id="custom-model-123"
            )

            orchestrator.execute(request)

            # Check that the custom model was used
            call_kwargs = mock_handler.execute.call_args[1]
            assert call_kwargs["model_name"] == "custom-model-123"
        finally:
            handler_registry.get_handler = original_get_handler

    def test_model_alias_resolution(self):
        """Test that model aliases are resolved correctly."""
        from llm_orchestrator.config import get_config
        config = get_config()

        # Test gemini alias
        resolved = config.resolve_model_alias("gemini")
        assert resolved == "gemini-2.0-flash-exp"

        # Test openai alias
        resolved = config.resolve_model_alias("openai")
        assert resolved == "gpt-4o-mini"

        # Test unknown alias (should return as-is)
        resolved = config.resolve_model_alias("unknown-model")
        assert resolved == "unknown-model"


class TestResponseStructure:
    """Test response structure and metadata."""

    def test_response_has_required_fields(self):
        """Test that response contains all required fields."""
        orchestrator = LLMOrchestrator()

        # Mock handler
        mock_handler_class = Mock()
        mock_handler = MagicMock()
        mock_result = {"is_valid": True, "issues": [], "suggestions": []}
        mock_handler.execute.return_value = mock_result
        mock_handler_class.return_value = mock_handler

        from llm_orchestrator.core import handler_registry
        original_get_handler = handler_registry.get_handler
        handler_registry.get_handler = Mock(return_value=mock_handler_class)

        try:
            request = LLMRequest(
                feature="pillars",
                operation="validate",
                data={"name": "test", "description": "test"},
                model_id="gemini"
            )

            response = orchestrator.execute(request)

            # Check response structure
            assert response.success is True
            assert response.results == mock_result
            assert response.metadata is not None
            assert response.metadata.execution_time_ms >= 0
            assert response.metadata.mode == "monolithic"
            assert len(response.metadata.models_used) > 0
        finally:
            handler_registry.get_handler = original_get_handler


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
