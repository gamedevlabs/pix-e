"""
Tests for MonolithicSPARCHandler.

Tests monolithic SPARC evaluation including input validation and prompt building.
"""

import pytest

from llm.exceptions import InvalidRequestError
from sparc.llm.handlers import MonolithicSPARCHandler


class TestMonolithicSPARCHandler:
    """Test MonolithicSPARCHandler functionality."""

    def test_handler_has_correct_metadata(self, mock_model_manager):
        """Test that handler has correct operation metadata."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        assert handler.operation_id == "sparc.monolithic"
        assert handler.operation_name == "monolithic"
        assert handler.temperature == 0
        assert handler.response_schema.__name__ == "MonolithicSPARCResponse"

    def test_validate_input_with_valid_data(
        self, mock_model_manager, sample_sparc_data
    ):
        """Test that validate_input accepts valid game text."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        # Should not raise any exception
        handler.validate_input(sample_sparc_data)

    def test_validate_input_rejects_missing_game_text(self, mock_model_manager):
        """Test that validate_input rejects data without game_text."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input({})

        assert "game_text" in str(exc_info.value)

    def test_validate_input_rejects_empty_game_text(self, mock_model_manager):
        """Test that validate_input rejects empty game_text."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input({"game_text": ""})

        assert "game_text" in str(exc_info.value)

    def test_build_prompt_includes_game_text(
        self, mock_model_manager, sample_sparc_data
    ):
        """Test that build_prompt includes the game text."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_sparc_data)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert sample_sparc_data["game_text"] in prompt
        # Ensure template markers are filled
        assert "%s" not in prompt

    def test_build_prompt_uses_monolithic_template(
        self, mock_model_manager, sample_sparc_data
    ):
        """Test that build_prompt uses the monolithic SPARC template."""
        handler = MonolithicSPARCHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_sparc_data)

        # Should contain key SPARC aspects from monolithic prompt
        assert "player experience" in prompt.lower()
        assert "theme" in prompt.lower()
        assert "gameplay" in prompt.lower()
        # Should contain instruction about evaluation
        assert "evaluate" in prompt.lower() or "check" in prompt.lower()
