"""
Tests for LLMResponse validation and structure.

Tests response format, required fields, and Pydantic model behavior.
"""

from unittest.mock import Mock

from llm import LLMOrchestrator
from llm.types import LLMRequest, LLMResponse


class TestResponseStructure:
    """Test LLMResponse structure and fields."""

    def test_response_has_required_fields(self, mock_model_manager):
        """Test that response contains all required fields."""
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

        # Check required fields
        assert hasattr(response, "success")
        assert hasattr(response, "results")
        assert hasattr(response, "metadata")
        assert hasattr(response, "errors")
        assert hasattr(response, "warnings")

    def test_successful_response_structure(self, mock_model_manager):
        """Test structure of a successful response."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {
            "hasStructureIssue": False,
            "content_feedback": "Good pillar",
        }
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        # Successful response
        assert response.success is True
        assert isinstance(response.results, dict)
        assert response.results is not None
        assert len(response.errors) == 0

    def test_response_is_pydantic_model(self, mock_model_manager):
        """Test that response is a Pydantic model."""
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

        # Should be a Pydantic model
        assert isinstance(response, LLMResponse)
        assert hasattr(response, "model_dump")
        assert callable(response.model_dump)

    def test_response_can_be_serialized(self, mock_model_manager):
        """Test that response can be serialized to dict."""
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

        # Should be serializable
        response_dict = response.model_dump()
        assert isinstance(response_dict, dict)
        assert "success" in response_dict
        assert "results" in response_dict
        assert "metadata" in response_dict


class TestResponseResults:
    """Test response results field."""

    def test_results_contains_handler_output(self, mock_model_manager):
        """Test that results field contains handler output."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {
            "hasStructureIssue": False,
            "content_feedback": "Test feedback",
        }
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        # Results should contain handler output
        assert isinstance(response.results, dict)
        assert "hasStructureIssue" in response.results
        assert "content_feedback" in response.results
        assert response.results["content_feedback"] == "Test feedback"

    def test_results_is_always_dict(self, mock_model_manager):
        """Test that results is always a dictionary."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        mock_result = Mock()
        mock_result.model_dump.return_value = {"key": "value"}
        mock_model_manager.generate_structured_with_model.return_value = mock_result

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="gemini-2.0-flash-exp",
        )

        response = orchestrator.execute(request)

        # Results must be a dict
        assert isinstance(response.results, dict)
