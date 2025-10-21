"""
Tests for addition and context evaluation handlers.

Tests SuggestAdditionsHandler and EvaluateContextHandler.
"""

from unittest.mock import Mock

from pillars.llm.handlers import (
    EvaluateContextHandler,
    SuggestAdditionsHandler,
)


class TestSuggestAdditionsHandler:
    """Test SuggestAdditionsHandler functionality."""

    def test_handler_has_correct_metadata(self):
        """Test that handler has correct operation metadata."""
        handler = SuggestAdditionsHandler(Mock())

        assert handler.operation_id == "pillars.suggest_additions"
        assert handler.version == "1.0.0"
        assert handler.description != ""

    def test_handler_validates_input_with_valid_data(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test that handler accepts valid input data."""
        handler = SuggestAdditionsHandler(mock_model_manager)

        # Should not raise
        handler.validate_input(sample_evaluation_data)

    def test_handler_builds_prompt(self, mock_model_manager, sample_evaluation_data):
        """Test that handler builds a prompt from data."""
        handler = SuggestAdditionsHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_evaluation_data)

        assert isinstance(prompt, str)
        assert sample_evaluation_data["context"] in prompt
        assert sample_evaluation_data["pillars_text"] in prompt


class TestEvaluateContextHandler:
    """Test EvaluateContextHandler functionality."""

    def test_handler_has_correct_metadata(self):
        """Test that handler has correct operation metadata."""
        handler = EvaluateContextHandler(Mock())

        assert handler.operation_id == "pillars.evaluate_context"
        assert handler.version == "1.0.0"
        assert handler.description != ""

    def test_handler_validates_input_with_valid_data(
        self, mock_model_manager, sample_evaluation_data
    ):
        """Test that handler accepts valid input data."""
        handler = EvaluateContextHandler(mock_model_manager)

        # Should not raise
        handler.validate_input(sample_evaluation_data)

    def test_handler_builds_prompt(self, mock_model_manager, sample_evaluation_data):
        """Test that handler builds a prompt from data."""
        handler = EvaluateContextHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_evaluation_data)

        assert isinstance(prompt, str)
        assert sample_evaluation_data["context"] in prompt
        assert sample_evaluation_data["pillars_text"] in prompt
