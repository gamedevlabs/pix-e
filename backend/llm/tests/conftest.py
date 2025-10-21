"""
Pytest configuration for LLM orchestrator tests.

Provides fixtures for mocking LLM components and testing utilities.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture(scope="session", autouse=True)
def ensure_handlers_registered():
    """Ensure pillar handlers are registered once per session."""
    # Import pillars handlers to trigger registration
    from pillars.llm import handlers  # noqa: F401

    yield


@pytest.fixture
def isolated_registry():
    """
    Fixture for tests that need an isolated registry.

    Use this explicitly in tests that need registry isolation,
    rather than as autouse.
    """
    from llm.handler_registry import get_registry

    registry = get_registry()
    # Store original state
    original_handlers = registry._handlers.copy()

    yield registry

    # Restore original state after test
    registry._handlers = original_handlers


@pytest.fixture
def mock_model_manager():
    """Create a mock ModelManager for testing handlers."""
    mock_manager = Mock()

    # Mock generate_structured_with_model to return a mock response
    mock_manager.generate_structured_with_model = Mock(return_value=Mock())

    # Mock list_available_models
    mock_manager.list_available_models = Mock(
        return_value=[
            Mock(name="gemini-2.0-flash-exp", provider="gemini", type="cloud"),
            Mock(name="gpt-4o-mini", provider="openai", type="cloud"),
        ]
    )

    return mock_manager


@pytest.fixture
def sample_pillar_data():
    """Sample pillar data for testing."""
    return {
        "name": "Core Mechanic",
        "description": "Players solve environmental puzzles using physics",
    }


@pytest.fixture
def sample_pillars_text():
    """Sample formatted pillars text for evaluation operations."""
    return """1. Core Mechanic: Players solve environmental puzzles using physics
2. Player Experience: Create moments of discovery and achievement
3. Visual Style: Minimalist art with focus on lighting and shadow"""


@pytest.fixture
def sample_context():
    """Sample context for pillar operations."""
    return "A puzzle-adventure game with physics-based mechanics"


@pytest.fixture
def mock_provider():
    """Create a mock LLM provider for testing."""
    mock = Mock()
    mock.provider_name = "mock"
    mock.provider_type = "local"
    mock.is_available = Mock(return_value=True)
    mock.generate_text = Mock(return_value="Mock LLM response")
    mock.generate_structured = Mock(return_value=Mock())
    return mock
