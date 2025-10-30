"""
Simplified unit test for SPARC quick scan graph aggregation logic.

Tests the aggregation logic using mock objects without full schema validation.
"""

from unittest.mock import Mock

from llm.types import AgentResult, LLMRequest
from sparc.llm.graphs import SPARCQuickScanGraph


def test_graph_build_agents():
    """Test that graph builds all 10 agents."""
    print("Testing SPARCQuickScanGraph.build_agents()...")

    # Create mock dependencies
    config = Mock()
    model_manager = Mock()
    graph = SPARCQuickScanGraph(model_manager, config)

    # Create request
    request = LLMRequest(
        feature="sparc",
        operation="quick_scan",
        data={"game_text": "Test game"},
        model_id="gpt-4o-mini",
    )

    # Test build_agents
    agents = graph.build_agents(request)

    assert len(agents) == 10, f"Expected 10 agents, got {len(agents)}"
    print(f"✅ Built {len(agents)} agents")

    # Verify agent names
    expected_names = {
        "player_experience",
        "theme",
        "purpose",
        "gameplay",
        "goals_challenges_rewards",
        "place",
        "story_narrative",
        "unique_features",
        "art_direction",
        "opportunities_risks",
    }
    actual_names = {agent.name for agent in agents}
    assert actual_names == expected_names, f"Agent names mismatch: {actual_names}"
    print("✅ All expected agent names present\n")


def test_graph_aggregation():
    """Test that graph correctly aggregates agent results."""
    print("Testing SPARCQuickScanGraph.aggregate()...")

    # Create mock dependencies
    config = Mock()
    model_manager = Mock()
    graph = SPARCQuickScanGraph(model_manager, config)

    # Create mock agent results as dictionaries (simulating model_dump())
    def create_mock_response(score, issues=None, suggestions=None):
        return {
            "score": score,
            "issues": issues or ["Issue 1", "Issue 2"],
            "suggestions": suggestions or ["Suggestion 1"],
        }

    agent_results = [
        AgentResult(
            agent_name="player_experience",
            success=True,
            data=create_mock_response(85),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="theme",
            success=True,
            data=create_mock_response(70),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="purpose",
            success=True,
            data=create_mock_response(90),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="gameplay",
            success=True,
            data=create_mock_response(60),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="goals_challenges_rewards",
            success=True,
            data=create_mock_response(75),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="place",
            success=True,
            data=create_mock_response(80),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="story_narrative",
            success=True,
            data=create_mock_response(65),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="unique_features",
            success=True,
            data=create_mock_response(55),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="art_direction",
            success=True,
            data=create_mock_response(70),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="opportunities_risks",
            success=True,
            data=create_mock_response(75),
            execution_time_ms=100,
        ),
    ]

    # Create request
    request = LLMRequest(
        feature="sparc",
        operation="quick_scan",
        data={"game_text": "Test game"},
        model_id="gpt-4o-mini",
    )

    # Test aggregation
    result = graph.aggregate(agent_results, request)

    # Verify structure
    assert "readiness_score" in result, "Missing readiness_score"
    assert "readiness_status" in result, "Missing readiness_status"
    assert "aspect_scores" in result, "Missing aspect_scores"
    assert "strongest_aspects" in result, "Missing strongest_aspects"
    assert "weakest_aspects" in result, "Missing weakest_aspects"
    assert "critical_gaps" in result, "Missing critical_gaps"
    assert "estimated_time_to_ready" in result, "Missing estimated_time_to_ready"
    assert "next_steps" in result, "Missing next_steps"

    print("✅ All required fields present")

    # Check readiness score (average: 72.5, rounded to 72 or 73)
    readiness = result["readiness_score"]
    assert 70 <= readiness <= 75, f"Unexpected readiness score: {readiness}"
    print(f"✅ Readiness score: {readiness}/100")

    # Check readiness status
    status = result["readiness_status"]
    assert status in [
        "Ready",
        "Nearly Ready",
        "Needs Work",
        "Not Ready",
    ], f"Invalid status: {status}"
    print(f"✅ Readiness status: {status}")

    # Check aspect scores
    aspect_scores = result["aspect_scores"]
    assert (
        len(aspect_scores) == 10
    ), f"Expected 10 aspect scores, got {len(aspect_scores)}"  # noqa: E501
    print(f"✅ Aspect scores: {len(aspect_scores)} aspects")

    # Verify aspect scores have all required fields
    for aspect_score in aspect_scores:
        assert "aspect" in aspect_score, "Missing aspect name"
        assert "score" in aspect_score, "Missing score"
        assert "status" in aspect_score, "Missing status"
        assert "key_issues" in aspect_score, "Missing key_issues"
        assert "priority" in aspect_score, "Missing priority"

    print("✅ All aspect scores have required fields")

    # Check strongest/weakest
    strongest = result["strongest_aspects"]
    weakest = result["weakest_aspects"]
    assert len(strongest) == 3, f"Expected 3 strongest, got {len(strongest)}"
    assert len(weakest) == 3, f"Expected 3 weakest, got {len(weakest)}"
    print(f"✅ Strongest: {', '.join(strongest)}")
    print(f"✅ Weakest: {', '.join(weakest)}")

    # Unique features should be weakest (score 55)
    assert "unique_features" in weakest, "unique_features should be in weakest"
    print("✅ Correctly identified weakest aspect")

    # Purpose should be strongest (score 90)
    assert "purpose" in strongest, "purpose should be in strongest"
    print("✅ Correctly identified strongest aspect")

    # Check individual aspect results
    assert result["player_experience"] is not None, "Missing player_experience"
    assert result["gameplay"] is not None, "Missing gameplay"
    print("✅ Individual aspect results included\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPARC Quick Scan Graph Unit Tests (Simplified)")
    print("=" * 60 + "\n")

    test_graph_build_agents()
    test_graph_aggregation()

    print("=" * 60)
    print("✨ All unit tests passed!")
    print("=" * 60)
