"""
Pytest configuration for llm_orchestrator tests.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture(autouse=True)
def reset_handler_registry():
    """Reset handler registry before each test."""
    from llm_orchestrator.core.handler_registry import get_registry
    registry = get_registry()
    # Store original state
    original_handlers = registry._handlers.copy()

    yield

    # Restore original state after test
    registry._handlers = original_handlers
