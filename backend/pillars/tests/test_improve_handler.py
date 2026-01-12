"""
Tests for ImprovePillarHandler.

Tests pillar improvement operation including input validation and prompt building.
"""

from unittest.mock import Mock

import pytest

from llm.exceptions import InvalidRequestError
from llm.types import LLMRequest
from pillars.llm.handlers import ImprovePillarWithExplanationHandler


class TestImprovePillarHandler:
    """Test ImprovePillarHandler functionality."""

    def test_handler_has_correct_metadata(self):
        """Test that handler has correct operation metadata."""
        handler = ImprovePillarWithExplanationHandler(Mock())

        assert handler.operation_id == "pillars.improve_explained"
        assert handler.version == "1.0.0"
        assert handler.description != ""
        assert handler.response_schema is not None

    def test_handler_validates_input_with_valid_data(
        self, mock_model_manager, sample_pillar_data
    ):
        """Test that handler accepts valid input data."""
        handler = ImprovePillarWithExplanationHandler(mock_model_manager)

        # Should not raise
        handler.validate_input(sample_pillar_data)

    def test_handler_validates_input_rejects_missing_name(self, mock_model_manager):
        """Test that handler rejects data missing 'name'."""
        handler = ImprovePillarWithExplanationHandler(mock_model_manager)

        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input({"description": "Test"})

        assert "name" in str(exc_info.value).lower()

    def test_handler_validates_input_rejects_missing_description(
        self, mock_model_manager
    ):
        """Test that handler rejects data missing 'description'."""
        handler = ImprovePillarWithExplanationHandler(mock_model_manager)

        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input({"name": "Test"})

        assert "description" in str(exc_info.value).lower()

    def test_handler_builds_prompt(self, mock_model_manager, sample_pillar_data):
        """Test that handler builds a prompt from data."""
        handler = ImprovePillarWithExplanationHandler(mock_model_manager)

        prompt = handler.build_prompt(sample_pillar_data)

        # Prompt should contain pillar info
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert sample_pillar_data["name"] in prompt
        assert sample_pillar_data["description"] in prompt

    def test_handler_execute_returns_improved_pillar(
        self, mock_model_manager, sample_pillar_data
    ):
        """Test that handler returns improved pillar."""
        handler = ImprovePillarWithExplanationHandler(mock_model_manager)

        # Mock the LLM response with improved pillar
        mock_result = Mock()
        mock_result.name = "Core Mechanic (Improved)"
        mock_result.description = "Enhanced description with better clarity"
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        result = handler.execute(
            data=sample_pillar_data, model_name="gemini-2.0-flash-exp"
        )

        # Should return the improved pillar
        assert result == mock_result
        assert mock_model_manager.generate_structured_with_model.called


class TestImproveHandlerIntegration:
    """Test ImprovePillarHandler integration with orchestrator."""

    def test_improve_via_orchestrator(self, mock_model_manager, sample_pillar_data):
        """Test improving a pillar via orchestrator."""
        from llm import LLMOrchestrator

        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        # Mock the result
        mock_result = Mock()
        mock_result.model_dump.return_value = {
            "name": "Core Mechanic",
            "description": "Improved description with better structure",
        }
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="improve",
            data=sample_pillar_data,
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        # Should succeed
        assert response.success is True
        assert "name" in response.results
        assert "description" in response.results
