"""
Unit test for SPARC quick scan workflow aggregation logic.

Tests the aggregation logic without making actual LLM calls.
"""

from unittest.mock import Mock

from llm.types import AgentResult, LLMRequest
from sparc.llm.schemas.gameplay import GameplayResponse, GoalsChallengesRewardsResponse
from sparc.llm.schemas.player_experience import (
    PlayerExperienceResponse,
    PurposeResponse,
    ThemeResponse,
)
from sparc.llm.schemas.visual_meta import (
    ArtDirectionResponse,
    OpportunitiesRisksResponse,
    UniqueFeaturesResponse,
)
from sparc.llm.schemas.world import PlaceResponse, StoryNarrativeResponse
from sparc.llm.workflows import SPARCQuickScanWorkflow


def test_workflow_build_agents():
    """Test that workflow builds all 10 agents."""
    print("Testing SPARCQuickScanWorkflow.build_agents()...")

    # Create mock dependencies
    config = Mock()
    model_manager = Mock()
    workflow = SPARCQuickScanWorkflow(model_manager, config)

    # Create request
    request = LLMRequest(
        feature="sparc",
        operation="quick_scan",
        data={"game_text": "Test game"},
        model_id="gpt-4o-mini",
    )

    # Test build_agents
    agents = workflow.build_agents(request)

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


def test_workflow_aggregation():
    """Test that workflow correctly aggregates agent results."""
    print("Testing SPARCQuickScanWorkflow.aggregate()...")

    # Create mock dependencies
    config = Mock()
    model_manager = Mock()
    workflow = SPARCQuickScanWorkflow(model_manager, config)

    # Create mock agent results
    agent_results = [
        AgentResult(
            agent_name="player_experience",
            success=True,
            data=PlayerExperienceResponse(
                active_form=True,
                emotional_focus="Test focus",
                clarity_score=85,
                high_concept="Test concept",
                score=85,
                issues=["Issue 1", "Issue 2"],
                suggestions=["Suggestion 1"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="theme",
            success=True,
            data=ThemeResponse(
                theme_elements=["Element 1"],
                consistency_score=70,
                score=70,
                issues=["Theme issue"],
                suggestions=["Theme suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="purpose",
            success=True,
            data=PurposeResponse(
                purpose_statement="Test purpose",
                clarity_score=90,
                score=90,
                issues=[],
                suggestions=["Purpose suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="gameplay",
            success=True,
            data=GameplayResponse(
                core_verbs=["jump", "shoot"],
                mechanics_clarity=60,
                thirty_second_loop="Test loop",
                score=60,
                issues=["Gameplay issue 1", "Gameplay issue 2"],
                suggestions=["Improve mechanics"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="goals_challenges_rewards",
            success=True,
            data=GoalsChallengesRewardsResponse(
                objectives=["Objective 1"],
                obstacles=["Obstacle 1"],
                rewards=["Reward 1"],
                integration_quality=75,
                score=75,
                issues=["GCR issue"],
                suggestions=["GCR suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="place",
            success=True,
            data=PlaceResponse(
                environment_settings=["Setting 1"],
                location_specificity=80,
                score=80,
                issues=["Place issue"],
                suggestions=["Place suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="story_narrative",
            success=True,
            data=StoryNarrativeResponse(
                story_summary="Test story",
                storytelling_methods=["Environmental"],
                completeness_score=65,
                score=65,
                issues=["Story issue"],
                suggestions=["Story suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="unique_features",
            success=True,
            data=UniqueFeaturesResponse(
                claimed_features=["Feature 1"],
                uniqueness_validation="Valid",
                score=55,
                issues=["Uniqueness issue 1", "Uniqueness issue 2"],
                suggestions=["Uniqueness suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="art_direction",
            success=True,
            data=ArtDirectionResponse(
                art_style="Stylized",
                color_palette="Dark",
                score=70,
                issues=["Art issue"],
                suggestions=["Art suggestion"],
            ),
            execution_time_ms=100,
        ),
        AgentResult(
            agent_name="opportunities_risks",
            success=True,
            data=OpportunitiesRisksResponse(
                market_opportunities=["Opportunity 1"],
                risks=["Risk 1"],
                score=75,
                issues=["Risk issue"],
                suggestions=["Risk suggestion"],
            ),
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
    result = workflow.aggregate(agent_results, request)

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

    # Check individual aspect results
    assert result["player_experience"] is not None, "Missing player_experience"
    assert result["gameplay"] is not None, "Missing gameplay"
    print("✅ Individual aspect results included\n")


if __name__ == "__main__":
    print("=" * 60)
    print("SPARC Quick Scan Workflow Unit Tests")
    print("=" * 60 + "\n")

    test_workflow_build_agents()
    test_workflow_aggregation()

    print("=" * 60)
    print("✨ All unit tests passed!")
    print("=" * 60)
