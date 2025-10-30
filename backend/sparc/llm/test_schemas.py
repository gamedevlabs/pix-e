"""
Test script for SPARC schemas.

Validates that all schemas can be instantiated and validated correctly.
"""

from sparc.llm.schemas import (
    ArtDirectionResponse,
    AspectScore,
    ConsistencyIssue,
    GameplayResponse,
    GoalsChallengesRewardsResponse,
    MonolithicSPARCResponse,
    OpportunitiesRisksResponse,
    PlaceResponse,
    PlayerExperienceResponse,
    PurposeResponse,
    SPARCQuickScanResponse,
    StoryNarrativeResponse,
    ThemeResponse,
    UniqueFeaturesResponse,
)


def test_player_experience_schema():
    """Test PlayerExperienceResponse schema."""
    data = {
        "current_description": "Player fights enemies",
        "is_player_active_form": False,
        "emotional_focus_present": False,
        "emotional_keywords": [],
        "improved_description": "I engage in tactical combat...",
        "high_concept_statement": "Dark Souls meets Returnal",
        "clarity_score": 65,
        "issues": ["Not in active form", "Lacks emotional depth"],
        "suggestions": ["Rewrite in first person", "Add emotional context"],
    }
    response = PlayerExperienceResponse(**data)
    assert response.clarity_score == 65
    print("✅ PlayerExperienceResponse validated")


def test_theme_schema():
    """Test ThemeResponse schema."""
    data = {
        "dominant_theme": "Isolation and perseverance",
        "dominant_theme_clarity": 80,
        "secondary_themes": ["Discovery", "Mystery"],
        "theme_consistency": 75,
        "missing_theme_elements": ["How theme manifests in gameplay"],
        "suggestions": ["Define theme in art direction"],
    }
    response = ThemeResponse(**data)
    assert response.dominant_theme_clarity == 80
    print("✅ ThemeResponse validated")


def test_gameplay_schema():
    """Test GameplayResponse schema."""
    data = {
        "core_verbs": ["explore", "fight", "adapt"],
        "core_mechanics_identified": ["Combat", "Exploration", "Resource management"],
        "thirty_second_gameplay": "Player explores, finds enemy, fights...",
        "level_core_mechanics": [],
        "mechanics_clarity": 70,
        "gameplay_loop_complete": True,
        "missing_mechanics": ["Progression system"],
        "suggestions": ["Define upgrade mechanics"],
    }
    response = GameplayResponse(**data)
    assert len(response.core_verbs) == 3
    print("✅ GameplayResponse validated")


def test_quick_scan_schema():
    """Test SPARCQuickScanResponse schema."""
    # Create individual aspect responses
    player_exp = PlayerExperienceResponse(
        current_description="Test",
        is_player_active_form=True,
        emotional_focus_present=True,
        emotional_keywords=["tension"],
        improved_description="Improved",
        high_concept_statement="Concept",
        clarity_score=80,
        issues=[],
        suggestions=[],
    )

    theme = ThemeResponse(
        dominant_theme="Test Theme",
        dominant_theme_clarity=75,
        secondary_themes=[],
        theme_consistency=70,
        missing_theme_elements=[],
        suggestions=[],
    )

    gameplay = GameplayResponse(
        core_verbs=["test"],
        core_mechanics_identified=[],
        thirty_second_gameplay="Test gameplay",
        level_core_mechanics=[],
        mechanics_clarity=60,
        gameplay_loop_complete=False,
        missing_mechanics=[],
        suggestions=[],
    )

    place = PlaceResponse(
        environment_setting="Space station",
        key_locations=["Hub", "Engine room"],
        location_specificity=70,
        setting_clarity=80,
        location_variety=65,
        missing_elements=[],
        suggestions=[],
    )

    unique = UniqueFeaturesResponse(
        claimed_unique_features=["Time loop"],
        validated_uniqueness=[],
        differentiation_from_existing="Unique approach",
        genre_improvements=[],
        defining_elements=["Feature 1"],
        uniqueness_score=75,
        needs_validation=[],
        suggestions=[],
    )

    story = StoryNarrativeResponse(
        story_summary="Test story",
        storytelling_methods=["Environmental"],
        environment_description="Test environment",
        history_before_arrival="History",
        player_arrival_how="Test arrival",
        player_arrival_why="Test reason",
        player_overall_goal="Test goal",
        communication_method="Test method",
        navigation_flow="Test navigation",
        key_events=[],
        story_completeness=50,
        missing_story_elements=[],
        suggestions=[],
    )

    goals = GoalsChallengesRewardsResponse(
        objectives=[],
        obstacles=[],
        rewards=[],
        story_integration=60,
        communication_strategy="Test strategy",
        challenge_balance=70,
        structure_completeness=55,
        missing_elements=[],
        suggestions=[],
    )

    art = ArtDirectionResponse(
        art_style="Stylized",
        visual_uniqueness_elements=["Element 1"],
        color_palette={"primary": "blue", "secondary": "red"},
        lighting_ratio="High contrast",
        temperature="Cool",
        reference_suggestions=[],
        art_direction_completeness=45,
        style_clarity=60,
        missing_elements=[],
        suggestions=[],
    )

    purpose = PurposeResponse(
        project_purpose="Test purpose",
        creator_motivation="Test motivation",
        team_appeal="Test appeal",
        creator_goals="Test goals",
        purpose_clarity=70,
        motivation_strength=80,
        missing_elements=[],
        suggestions=[],
    )

    opps_risks = OpportunitiesRisksResponse(
        opportunities=[],
        risks=[],
        opportunity_score=65,
        risk_score=40,
        risk_mitigation_completeness=70,
        critical_risks=[],
        missing_analysis=[],
        suggestions=[],
    )

    # Create aspect scores
    aspect_scores = [
        AspectScore(
            aspect="player_experience",
            score=80,
            status="strong",
            key_issues=[],
            priority="low",
        ),
        AspectScore(
            aspect="theme",
            score=75,
            status="adequate",
            key_issues=[],
            priority="medium",
        ),
    ]

    # Create quick scan response
    quick_scan = SPARCQuickScanResponse(
        readiness_score=65,
        readiness_status="Needs Work",
        aspect_scores=aspect_scores,
        strongest_aspects=["player_experience", "theme"],
        weakest_aspects=["art_direction", "story_narrative"],
        critical_gaps=["Define concrete locations"],
        estimated_time_to_ready="6-8 hours",
        next_steps=["Develop art direction", "Define locations"],
        player_experience=player_exp,
        theme=theme,
        gameplay=gameplay,
        place=place,
        unique_features=unique,
        story_narrative=story,
        goals_challenges_rewards=goals,
        art_direction=art,
        purpose=purpose,
        opportunities_risks=opps_risks,
    )

    assert quick_scan.readiness_score == 65
    assert len(quick_scan.aspect_scores) == 2
    print("✅ SPARCQuickScanResponse validated")


def test_consistency_issue_schema():
    """Test ConsistencyIssue schema."""
    data = {
        "aspects_involved": ["theme", "art_direction"],
        "issue_type": "misalignment",
        "description": "Theme suggests horror but art is cartoonish",
        "severity": "high",
        "suggested_resolution": "Align art style with horror theme",
    }
    issue = ConsistencyIssue(**data)
    assert issue.severity == "high"
    print("✅ ConsistencyIssue validated")


def test_monolithic_schema():
    """Test MonolithicSPARCResponse schema."""
    data = {
        "overall_assessment": "Concept needs significant development",
        "aspects_evaluated": {
            "player_experience": "Lacks emotional depth",
            "theme": "Unclear",
        },
        "missing_aspects": ["Place", "Art Direction"],
        "suggestions": ["Define theme", "Add locations"],
        "additional_details": ["Consider visual style"],
        "readiness_verdict": "Needs more work",
    }
    response = MonolithicSPARCResponse(**data)
    assert response.readiness_verdict == "Needs more work"
    print("✅ MonolithicSPARCResponse validated")


if __name__ == "__main__":
    print("Testing SPARC schemas...\n")

    test_player_experience_schema()
    test_theme_schema()
    test_gameplay_schema()
    test_consistency_issue_schema()
    test_monolithic_schema()
    test_quick_scan_schema()

    print("\n✨ All schemas validated successfully!")
