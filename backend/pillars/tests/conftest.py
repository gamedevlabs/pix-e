"""
Pytest configuration for pillar handler tests.

Provides fixtures for testing pillar-specific LLM operations.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_model_manager():
    """Create a mock ModelManager for testing pillar handlers."""
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
    """Sample pillar data for validate/improve operations."""
    return {
        "name": "Core Mechanic",
        "description": (
            "Players solve environmental puzzles using physics-based interactions"
        ),
    }


@pytest.fixture
def sample_pillars_text():
    """Sample formatted pillars text for evaluation operations."""
    return """1. Core Mechanic: Players solve environmental puzzles using physics
2. Player Experience: Create moments of discovery and achievement
3. Visual Style: Minimalist art with focus on lighting and shadow"""


@pytest.fixture
def sample_context():
    """Sample game context for pillar operations."""
    return "A puzzle-adventure game with physics-based mechanics"


@pytest.fixture
def sample_evaluation_data(sample_pillars_text, sample_context):
    """
    Sample data for evaluation operations.

    Used for completeness, contradictions, additions, and context evaluation.
    """
    return {
        "pillars_text": sample_pillars_text,
        "context": sample_context,
    }
