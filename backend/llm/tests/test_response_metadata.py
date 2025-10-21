"""
Tests for response metadata structure.

Tests ResponseMetadata fields, execution mode, and model tracking.
"""

from unittest.mock import Mock

from llm import LLMOrchestrator
from llm.types import LLMRequest


class TestResponseMetadata:
    """Test response metadata structure."""

    def test_metadata_has_required_fields(self, mock_model_manager):
        """Test that metadata contains required fields."""
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

        # Check metadata fields
        assert hasattr(response.metadata, "execution_time_ms")
        assert hasattr(response.metadata, "mode")
        assert hasattr(response.metadata, "models_used")

    def test_metadata_mode_is_valid(self, mock_model_manager):
        """Test that metadata.mode is a valid execution mode."""
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

        # Mode should be valid
        assert response.metadata.mode in ["monolithic", "agentic"]

    def test_metadata_models_used_is_list(self, mock_model_manager):
        """Test that metadata.models_used is a list."""
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

        # models_used should be a list
        assert isinstance(response.metadata.models_used, list)
        assert len(response.metadata.models_used) > 0
