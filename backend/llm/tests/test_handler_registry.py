"""
Tests for handler registry system.

Tests handler registration, discovery, and metadata extraction.
"""

import pytest

from llm.exceptions import UnknownOperationError
from llm.handler_registry import (
    get_handler,
    get_metadata,
    get_registry,
    list_features,
    list_metadata,
    list_operations,
)
from llm.operation_handler import BaseOperationHandler


class TestHandlerRegistration:
    """Test handler registration system."""

    def test_get_registry_returns_singleton(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_pillar_handlers_are_registered(self):
        """Test that pillar handlers are auto-registered."""
        registry = get_registry()

        # Check that pillar operations are registered
        assert registry.has_operation("pillars.validate")
        assert registry.has_operation("pillars.improve")
        assert registry.has_operation("pillars.evaluate_completeness")
        assert registry.has_operation("pillars.evaluate_contradictions")
        assert registry.has_operation("pillars.suggest_additions")
        assert registry.has_operation("pillars.evaluate_context")

    def test_get_handler_returns_correct_class(self):
        """Test that get_handler returns the correct handler class."""
        from pillars.llm.handlers import ValidatePillarHandler

        handler_class = get_handler("pillars.validate")
        assert handler_class == ValidatePillarHandler

    def test_get_unknown_handler_raises_error(self):
        """Test that getting unknown handler raises UnknownOperationError."""
        with pytest.raises(UnknownOperationError) as exc_info:
            get_handler("unknown.operation")

        assert exc_info.value.code == "UNKNOWN_OPERATION"
        assert "unknown" in str(exc_info.value).lower()


class TestHandlerMetadata:
    """Test handler metadata extraction."""

    def test_get_metadata_returns_operation_metadata(self):
        """Test that get_metadata returns correct metadata."""
        metadata = get_metadata("pillars.validate")

        assert metadata.operation_id == "pillars.validate"
        assert metadata.feature_id == "pillars"
        assert metadata.operation_name == "validate"
        assert metadata.version == "1.0.0"
        assert metadata.description != ""
        assert metadata.handler_class is not None

    def test_metadata_full_id(self):
        """Test that metadata full_id is formatted correctly."""
        metadata = get_metadata("pillars.validate")
        assert metadata.full_id == "pillars.validate@1.0.0"


class TestOperationListing:
    """Test operation discovery and listing."""

    def test_list_operations_returns_all_operations(self):
        """Test that list_operations returns all registered operations."""
        operations = list_operations()

        assert "pillars.validate" in operations
        assert "pillars.improve" in operations
        assert len(operations) >= 6  # At least 6 pillar operations

    def test_list_operations_filtered_by_feature(self):
        """Test that list_operations can filter by feature."""
        pillar_operations = list_operations(feature="pillars")

        assert all(op.startswith("pillars.") for op in pillar_operations)
        assert "pillars.validate" in pillar_operations
        assert len(pillar_operations) >= 6

    def test_list_features_returns_registered_features(self):
        """Test that list_features returns all feature IDs."""
        features = list_features()

        assert "pillars" in features
        assert isinstance(features, list)

    def test_list_metadata_returns_metadata_objects(self):
        """Test that list_metadata returns OperationMetadata objects."""
        metadata_list = list_metadata(feature="pillars")

        assert len(metadata_list) >= 6
        for metadata in metadata_list:
            assert metadata.operation_id.startswith("pillars.")
            assert metadata.feature_id == "pillars"
            assert metadata.version == "1.0.0"


class TestHandlerAutoRegistration:
    """Test automatic handler registration via __init_subclass__."""

    def test_handler_auto_registers_on_class_definition(
        self, isolated_registry, mock_model_manager
    ):
        """Test that defining a handler class auto-registers it."""

        # Create a test handler
        class TestHandler(BaseOperationHandler):
            operation_id = "test.operation"
            response_schema = type("TestSchema", (), {})

            def build_prompt(self, data):
                return "test prompt"

        # Check it was registered
        assert isolated_registry.has_operation("test.operation")

        # Verify we can get it
        handler_class = get_handler("test.operation")
        assert handler_class == TestHandler

    def test_handler_without_operation_id_not_registered(self, isolated_registry):
        """Test that handlers without operation_id are not registered."""
        initial_count = len(isolated_registry._handlers)

        # Create handler without operation_id
        class IncompleteHandler(BaseOperationHandler):
            # No operation_id
            response_schema = type("Schema", (), {})

            def build_prompt(self, data):
                return "test"

        # Should not increase registry count
        assert len(isolated_registry._handlers) == initial_count
