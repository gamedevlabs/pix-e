"""
Test script for SPARC monolithic handler.

Validates that the monolithic handler is properly configured.
"""

from unittest.mock import Mock

from sparc.llm.handlers import MonolithicSPARCHandler


def test_handler_configuration():
    """Test that monolithic handler is properly configured."""
    print("Testing MonolithicSPARCHandler configuration...\n")

    # Create mock model manager
    model_manager = Mock()
    handler = MonolithicSPARCHandler(model_manager)

    # Check operation ID
    assert (
        handler.operation_id == "sparc.monolithic"
    ), f"Wrong operation_id: {handler.operation_id}"
    print(f"✅ Operation ID: {handler.operation_id}")

    # Check operation name (extracted from ID)
    assert (
        handler.operation_name == "monolithic"
    ), f"Wrong operation name: {handler.operation_name}"  # noqa: E501
    print(f"✅ Operation name: {handler.operation_name}")

    # Check temperature
    assert handler.temperature == 0.3, f"Wrong temperature: {handler.temperature}"
    print(f"✅ Temperature: {handler.temperature}")

    # Check response schema
    assert hasattr(handler, "response_schema"), "Missing response_schema"
    print(f"✅ Response schema: {handler.response_schema.__name__}")

    # Test prompt building
    test_data = {"game_text": "A roguelike dungeon crawler with procedural generation"}
    prompt = handler.build_prompt(test_data)

    assert isinstance(prompt, str), "Prompt is not a string"
    assert len(prompt) > 0, "Prompt is empty"
    assert "A roguelike dungeon crawler" in prompt, "Game text not in prompt"
    assert "%s" not in prompt, "Prompt has unfilled template markers"

    print(f"✅ Prompt built successfully ({len(prompt)} chars)")
    print(f"   First 100 chars: {prompt[:100]}...")

    # Test input validation
    try:
        handler.validate_input(test_data)
        print("✅ Valid input accepted")
    except Exception as e:
        print(f"❌ Valid input rejected: {e}")
        raise

    # Test invalid input
    try:
        handler.validate_input({})
        print("❌ Invalid input accepted (should have failed)")
        raise AssertionError("Validation should have failed for empty input")
    except Exception:
        print("✅ Invalid input properly rejected")

    print()


if __name__ == "__main__":
    print("=" * 60)
    print("SPARC Monolithic Handler Tests")
    print("=" * 60 + "\n")

    test_handler_configuration()

    print("=" * 60)
    print("✨ All handler tests passed!")
    print("=" * 60)
