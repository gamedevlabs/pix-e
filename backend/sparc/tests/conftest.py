"""
Pytest configuration for SPARC tests.

Provides fixtures for testing SPARC handlers and views.
"""

from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_model_manager():
    """Create a mock ModelManager for testing SPARC handlers."""
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
def sample_game_text():
    """Sample game text for SPARC evaluation."""
    return """
    A roguelike dungeon crawler set in a procedurally generated dark fantasy world.
    Players explore dangerous dungeons filled with monsters, traps, and treasures.
    The game features permadeath, turn-based combat, and deep character customization.
    Each run is unique due to procedural generation of levels, items, and enemies.
    """


@pytest.fixture
def sample_sparc_data(sample_game_text):
    """Sample data for SPARC evaluation operations."""
    return {"game_text": sample_game_text.strip()}
