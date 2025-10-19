"""
Tests for operation handlers.
"""

from unittest.mock import Mock

import pytest
from llm_orchestrator.exceptions import InvalidRequestError
from llm_orchestrator.operations.pillars.handlers import (
    EvaluateCompletenessHandler,
    ImprovePillarHandler,
    ValidatePillarHandler,
)


class TestValidatePillarHandler:
    """Test ValidatePillarHandler."""

    def test_handler_attributes(self):
        """Test that handler has correct attributes."""
        model_manager = Mock()
        handler = ValidatePillarHandler(model_manager)

        assert handler.operation_id == "pillars.validate"
        assert handler.response_schema is not None

    def test_validate_input_success(self):
        """Test input validation passes with valid data."""
        model_manager = Mock()
        handler = ValidatePillarHandler(model_manager)

        data = {"name": "Test Pillar", "description": "Test description"}
        # Should not raise
        handler.validate_input(data)

    def test_validate_input_missing_name(self):
        """Test input validation fails when name is missing."""
        model_manager = Mock()
        handler = ValidatePillarHandler(model_manager)

        data = {"description": "Test description"}
        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input(data)

        assert "name" in str(exc_info.value).lower()

    def test_validate_input_missing_description(self):
        """Test input validation fails when description is missing."""
        model_manager = Mock()
        handler = ValidatePillarHandler(model_manager)

        data = {"name": "Test Pillar"}
        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input(data)

        assert "description" in str(exc_info.value).lower()

    def test_build_prompt(self):
        """Test that prompt is built correctly."""
        model_manager = Mock()
        handler = ValidatePillarHandler(model_manager)

        data = {"name": "Test Pillar", "description": "Test description"}
        prompt = handler.build_prompt(data)

        assert isinstance(prompt, str)
        assert "Test Pillar" in prompt
        assert "Test description" in prompt


class TestImprovePillarHandler:
    """Test ImprovePillarHandler."""

    def test_handler_attributes(self):
        """Test that handler has correct attributes."""
        model_manager = Mock()
        handler = ImprovePillarHandler(model_manager)

        assert handler.operation_id == "pillars.improve"
        assert handler.response_schema is not None

    def test_validate_input_success(self):
        """Test input validation passes with valid data."""
        model_manager = Mock()
        handler = ImprovePillarHandler(model_manager)

        data = {"name": "Test Pillar", "description": "Test description"}
        # Should not raise
        handler.validate_input(data)

    def test_build_prompt(self):
        """Test that prompt is built correctly."""
        model_manager = Mock()
        handler = ImprovePillarHandler(model_manager)

        data = {"name": "Test Pillar", "description": "Test description"}
        prompt = handler.build_prompt(data)

        assert isinstance(prompt, str)
        assert "Test Pillar" in prompt
        assert "Test description" in prompt


class TestEvaluateCompletenessHandler:
    """Test EvaluateCompletenessHandler."""

    def test_handler_attributes(self):
        """Test that handler has correct attributes."""
        model_manager = Mock()
        handler = EvaluateCompletenessHandler(model_manager)

        assert handler.operation_id == "pillars.evaluate_completeness"
        assert handler.response_schema is not None

    def test_validate_input_success(self):
        """Test input validation passes with valid data."""
        model_manager = Mock()
        handler = EvaluateCompletenessHandler(model_manager)

        data = {
            "pillars_text": "1. Pillar one\n2. Pillar two",
            "context": "Game design context",
        }
        # Should not raise
        handler.validate_input(data)

    def test_validate_input_missing_pillars_text(self):
        """Test input validation fails when pillars_text is missing."""
        model_manager = Mock()
        handler = EvaluateCompletenessHandler(model_manager)

        data = {"context": "Game design context"}
        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input(data)

        assert "pillars_text" in str(exc_info.value).lower()

    def test_validate_input_missing_context(self):
        """Test input validation fails when context is missing."""
        model_manager = Mock()
        handler = EvaluateCompletenessHandler(model_manager)

        data = {"pillars_text": "1. Pillar one"}
        with pytest.raises(InvalidRequestError) as exc_info:
            handler.validate_input(data)

        assert "context" in str(exc_info.value).lower()

    def test_build_prompt(self):
        """Test that prompt is built correctly."""
        model_manager = Mock()
        handler = EvaluateCompletenessHandler(model_manager)

        data = {
            "pillars_text": "1. Pillar one\n2. Pillar two",
            "context": "Game design context",
        }
        prompt = handler.build_prompt(data)

        assert isinstance(prompt, str)
        assert "Pillar one" in prompt
        assert "Game design context" in prompt


class TestHandlerRegistry:
    """Test handler registration system."""

    def test_handlers_are_registered(self):
        """Test that pillar handlers are registered."""
        from llm_orchestrator.core.handler_registry import get_handler

        # These should not raise
        validate_handler = get_handler("pillars.validate")
        assert validate_handler == ValidatePillarHandler

        improve_handler = get_handler("pillars.improve")
        assert improve_handler == ImprovePillarHandler

        completeness_handler = get_handler("pillars.evaluate_completeness")
        assert completeness_handler == EvaluateCompletenessHandler

    def test_unknown_handler_raises_error(self):
        """Test that getting unknown handler raises error."""
        from llm_orchestrator.core.handler_registry import get_handler
        from llm_orchestrator.exceptions import UnknownOperationError

        with pytest.raises(UnknownOperationError):
            get_handler("unknown.operation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
