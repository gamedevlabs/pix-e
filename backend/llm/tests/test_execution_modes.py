"""
Tests for orchestrator execution modes.

Tests handler mode execution, agent mode fallback, and mode validation.
"""

from unittest.mock import Mock

import pytest

from llm import LLMOrchestrator
from llm.exceptions import InvalidRequestError, UnknownOperationError
from llm.types import LLMRequest, LLMResponse


class TestHandlerModeExecution:
    """Test handler mode (monolithic) execution."""

    def test_execute_handler_mode_with_valid_operation(self, mock_model_manager):
        """Test executing a valid operation in handler mode."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        # Mock the handler execution - result must have model_dump()
        mock_result = Mock()
        mock_result.hasStructureIssue = False
        mock_result.structuralIssues = []
        mock_result.content_feedback = "Good pillar"
        mock_result.model_dump.return_value = {
            "hasStructureIssue": False,
            "structuralIssues": [],
            "content_feedback": "Good pillar",
        }

        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test description"},
            model_id="gemini-2.0-flash-exp",
            mode="monolithic",
        )

        response = orchestrator.execute(request)

        # Verify response structure
        assert isinstance(response, LLMResponse)
        assert response.success is True
        assert response.metadata is not None
        assert response.metadata.mode == "monolithic"

    def test_execute_uses_default_mode_when_not_specified(self, mock_model_manager):
        """Test that orchestrator uses default mode when not specified."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
            # mode not specified - should use default
        )

        response = orchestrator.execute(request)

        # Should succeed with default mode (monolithic)
        assert response.metadata.mode in ["monolithic", "agentic"]

    def test_execute_unknown_operation_raises_error(self, mock_model_manager):
        """Test that executing unknown operation raises error."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        request = LLMRequest(
            feature="unknown_feature",
            operation="unknown_operation",
            data={},
            model_id="gemini-2.0-flash-exp",
        )

        with pytest.raises(UnknownOperationError):
            orchestrator.execute(request)


class TestAgentModeExecution:
    """Test agent mode (agentic) execution."""

    def test_agent_mode_falls_back_to_handler_mode(self, mock_model_manager):
        """Test that agent mode currently falls back to handler mode."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"result": "success"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
            mode="agentic",
        )

        response = orchestrator.execute(request)

        # Should execute successfully
        assert response.success is True
        # Should have a warning about fallback
        assert response.warnings is not None
        assert len(response.warnings) > 0
        assert any("agent graph" in w.message.lower() for w in response.warnings)


class TestInvalidExecutionMode:
    """Test handling of invalid execution modes."""

    def test_invalid_mode_raises_error(self, mock_model_manager):
        """Test that invalid execution mode raises error."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
            mode="monolithic",
        )

        # Manually override to invalid mode to test internal validation
        request.mode = "invalid_mode"

        with pytest.raises(InvalidRequestError) as exc_info:
            orchestrator.execute(request)

        assert "unknown execution mode" in str(exc_info.value).lower()
        assert "invalid_mode" in str(exc_info.value)
