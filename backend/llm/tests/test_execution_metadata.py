"""
Tests for execution metadata tracking.

Tests execution time tracking and model usage tracking.
"""

from unittest.mock import Mock

from llm import LLMOrchestrator
from llm.types import LLMRequest


class TestExecutionTimeTracking:
    """Test execution time tracking."""

    def test_execution_time_is_tracked(self, mock_model_manager):
        """Test that execution time is tracked in metadata."""
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

        # Execution time should be tracked (can be 0 for very fast mock execution)
        assert response.metadata.execution_time_ms >= 0
        assert isinstance(response.metadata.execution_time_ms, int)

    def test_execution_time_is_reasonable(self, mock_model_manager):
        """Test that execution time is in reasonable range."""
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

        # Should be less than 1 second for mocked execution
        assert response.metadata.execution_time_ms < 1000


class TestModelUsageTracking:
    """Test model usage tracking in metadata."""

    def test_models_used_is_tracked(self, mock_model_manager):
        """Test that models used are tracked in metadata."""
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

        # Should track which models were used
        assert response.metadata.models_used is not None
        assert len(response.metadata.models_used) > 0
        assert response.metadata.models_used[0].name == "gemini-2.0-flash-exp"
