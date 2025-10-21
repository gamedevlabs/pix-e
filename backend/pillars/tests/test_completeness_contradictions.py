"""
Tests for completeness and contradiction evaluation handlers.

Tests EvaluateCompletenessHandler and EvaluateContradictionsHandler.
"""

from unittest.mock import Mock

import pytest

from llm.exceptions import InvalidRequestError
from llm.types import LLMRequest
from pillars.llm.handlers import (
    EvaluateCompletenessHandler,
    EvaluateContradictionsHandler,
)


class TestEvaluateCompletenessHandler:
    """Test EvaluateCompletenessHandler functionality."""

    def test_handler_has_correct_metadata(self):
        """Test that handler has correct operation metadata."""
        handler = EvaluateCompletenessHandler(Mock())

        assert handler.operation_id == "pillars.evaluate_completeness"
        assert handler.version == "1.0.0"
        assert handler.description != ""

    def test_handler_validates_input_with_valid_data(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test that handler accepts valid input data."""
        handler = EvaluateCompletenessHandler(mock_model_manager)

        # Should not raise
        handler.validate_input(sample_evaluation_data)

    def test_handler_validates_input_rejects_missing_fields(self, mock_model_manager):
        """Test that handler rejects missing required fields."""
        handler = EvaluateCompletenessHandler(mock_model_manager)

        with pytest.raises(InvalidRequestError):
            handler.validate_input({"pillars_text": "Test"})

        with pytest.raises(InvalidRequestError):
            handler.validate_input({"context": "Test"})

    def test_handler_builds_prompt(self, mock_model_manager, sample_evaluation_data):
        """Test that handler builds a prompt from data."""
        handler = EvaluateCompletenessHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_evaluation_data)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert sample_evaluation_data["context"] in prompt
        assert sample_evaluation_data["pillars_text"] in prompt

    def test_evaluate_completeness_via_orchestrator(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test completeness evaluation via orchestrator."""
        from llm import LLMOrchestrator

        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {
            "is_complete": True,
            "missing_aspects": [],
            "feedback": "Pillars cover all aspects",
        }
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="evaluate_completeness",
            data=sample_evaluation_data,
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        assert response.success is True
        assert "is_complete" in response.results


class TestEvaluateContradictionsHandler:
    """Test EvaluateContradictionsHandler functionality."""

    def test_handler_has_correct_metadata(self):
        """Test that handler has correct operation metadata."""
        handler = EvaluateContradictionsHandler(Mock())

        assert handler.operation_id == "pillars.evaluate_contradictions"
        assert handler.version == "1.0.0"
        assert handler.description != ""

    def test_handler_validates_input_with_valid_data(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test that handler accepts valid input data."""
        handler = EvaluateContradictionsHandler(mock_model_manager)

        # Should not raise
        handler.validate_input(sample_evaluation_data)

    def test_handler_builds_prompt(self, mock_model_manager, sample_evaluation_data):
        """Test that handler builds a prompt from data."""
        handler = EvaluateContradictionsHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_evaluation_data)

        assert isinstance(prompt, str)
        assert sample_evaluation_data["context"] in prompt
        assert sample_evaluation_data["pillars_text"] in prompt

    def test_evaluate_contradictions_via_orchestrator(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test contradiction evaluation via orchestrator."""
        from llm import LLMOrchestrator

        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {
            "has_contradictions": False,
            "contradictions": [],
            "feedback": "No contradictions found",
        }
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="evaluate_contradictions",
            data=sample_evaluation_data,
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        assert response.success is True
        assert "has_contradictions" in response.results
