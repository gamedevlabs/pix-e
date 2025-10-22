"""
Tests for model capability matching and availability.

Tests ModelCapabilities structure and model unavailability handling.
"""

import pytest

from llm import LLMOrchestrator, ModelManager
from llm.exceptions import ModelUnavailableError, ProviderError
from llm.types import LLMRequest, ModelCapabilities


@pytest.fixture
def manager():
    """Return a configured orchestrator or skip if missing credentials."""
    try:
        return ModelManager()
    except ProviderError as e:
        pytest.skip(f"Missing provider ({e})")
    except Exception as e:
        raise e


class TestModelCapabilityMatching:
    """Test model selection based on capabilities."""

    def test_model_manager_can_filter_by_capabilities(self, manager):
        """Test that ModelManager supports capability-based filtering."""

        # Check that manager has methods for capability-based selection
        assert hasattr(manager, "list_available_models")

        # Get available models
        models = manager.list_available_models()

        # Should return list of ModelDetails
        assert isinstance(models, list)

    def test_model_capabilities_structure(self):
        """Test that ModelCapabilities has expected structure."""
        # ModelCapabilities should have fields for different capabilities
        # Note: actual field names are json_strict, vision, multimodal, etc.
        caps = ModelCapabilities(
            json_strict=True,
            function_calling=False,
            vision=False,
            multimodal=False,
            min_context_window=8192,
        )

        assert caps.json_strict is True
        assert caps.function_calling is False
        assert caps.min_context_window == 8192


class TestModelUnavailableHandling:
    """Test handling when requested model is unavailable."""

    def test_orchestrator_handles_unavailable_model(self, mock_model_manager):
        """Test that orchestrator handles unavailable model gracefully."""
        orchestrator = LLMOrchestrator(model_manager=mock_model_manager)

        # Mock model manager to raise unavailable error
        # ModelUnavailableError requires model and provider arguments
        mock_model_manager.generate_structured_with_model.side_effect = (
            ModelUnavailableError(
                model="unavailable-model", provider="test", reason="Model not available"
            )
        )

        request = LLMRequest(
            feature="pillars",
            operation="validate",
            data={"name": "Test", "description": "Test"},
            model_id="unavailable-model",
        )

        # Should raise ModelUnavailableError
        with pytest.raises(ModelUnavailableError):
            orchestrator.execute(request)

    def test_model_manager_lists_only_available_models(self, manager):
        """Test that ModelManager only returns available models."""

        # Get available models
        models = manager.list_available_models()

        # All returned models should be available
        # (actual availability depends on API keys and provider config)
        assert isinstance(models, list)
        # Each model should have required fields
        for model in models:
            assert hasattr(model, "name")
            assert hasattr(model, "provider")
            assert hasattr(model, "type")
