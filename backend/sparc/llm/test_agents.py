"""
Test script for SPARC agents.

Validates that all agents can be instantiated and have correct configuration.
"""

from sparc.llm.agents import (
    GameplayAgent,
    PlaceAgent,
    PlayerExperienceAgent,
    ThemeAgent,
    UniqueFeaturesAgent,
)


def test_agent_instantiation():
    """Test that all agents can be instantiated."""
    print("Testing agent instantiation...\n")

    agents = [
        (PlayerExperienceAgent, "player_experience", 0.3),
        (ThemeAgent, "theme", 0.3),
        (GameplayAgent, "gameplay", 0.3),
        (PlaceAgent, "place", 0.3),
        (UniqueFeaturesAgent, "unique_features", 0.4),
    ]

    for agent_class, expected_name, expected_temp in agents:
        agent = agent_class()
        assert agent.name == expected_name, f"Name mismatch: {agent.name}"
        assert (
            agent.temperature == expected_temp
        ), f"Temperature mismatch: {agent.temperature}"
        assert hasattr(
            agent, "response_schema"
        ), f"{agent_class.__name__} missing response_schema"
        print(f"✅ {agent_class.__name__} initialized correctly")
        print(f"   - Name: {agent.name}")
        print(f"   - Temperature: {agent.temperature}")
        print(f"   - Schema: {agent.response_schema.__name__}")
        print()


def test_agent_prompt_building():
    """Test that agents can build prompts."""
    print("Testing prompt building...\n")

    sample_data = {"game_text": "A dark souls-like game set in a sci-fi universe."}

    agents = [
        PlayerExperienceAgent(),
        ThemeAgent(),
        GameplayAgent(),
        PlaceAgent(),
        UniqueFeaturesAgent(),
    ]

    for agent in agents:
        try:
            prompt = agent.build_prompt(sample_data)
            assert isinstance(prompt, str), f"{agent.name}: prompt not a string"
            assert len(prompt) > 0, f"{agent.name}: prompt is empty"
            assert "%s" not in prompt, f"{agent.name}: prompt has unfilled template"
            print(f"✅ {agent.name} built prompt ({len(prompt)} chars)")
        except Exception as e:
            print(f"❌ {agent.name} failed to build prompt: {e}")
            raise


def test_agent_validation():
    """Test agent input validation."""
    print("\nTesting input validation...\n")

    agent = PlayerExperienceAgent()

    # Test valid input
    try:
        agent.validate_input({"game_text": "Test game"})
        print("✅ Valid input accepted")
    except Exception as e:
        print(f"❌ Valid input rejected: {e}")
        raise

    # Test invalid input (missing game_text)
    try:
        agent.validate_input({})
        print("❌ Invalid input accepted (should have failed)")
        raise AssertionError("Validation should have failed")
    except Exception:
        print("✅ Invalid input properly rejected")


if __name__ == "__main__":
    print("=" * 60)
    print("SPARC Agent Tests")
    print("=" * 60 + "\n")

    test_agent_instantiation()
    test_agent_prompt_building()
    test_agent_validation()

    print("\n" + "=" * 60)
    print("✨ All agent tests passed!")
    print("=" * 60)
