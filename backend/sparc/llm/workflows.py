"""
SPARC evaluation workflows.

Contains agent workflows for orchestrating multi-agent SPARC evaluations.
"""

from typing import Any, Dict, List

from llm.agent_registry import register_workflow
from llm.agent_runtime import BaseAgent
from llm.agent_workflow import BaseAgentWorkflow
from llm.types import AgentResult, LLMRequest
from sparc.llm.agents import (
    ArtDirectionAgent,
    GameplayAgent,
    GoalsChallengesRewardsAgent,
    OpportunitiesRisksAgent,
    PlaceAgent,
    PlayerExperienceAgent,
    PurposeAgent,
    StoryNarrativeAgent,
    ThemeAgent,
    UniqueFeaturesAgent,
)
from sparc.llm.schemas.aggregated import AspectScore, SPARCQuickScanResponse


class SPARCQuickScanWorkflow(BaseAgentWorkflow):
    """
    Quick scan workflow that runs all 10 SPARC agents in parallel.

    This workflow provides a comprehensive evaluation by running specialized
    agents for each SPARC aspect simultaneously, then aggregating results.

    Execution mode: Simple parallel - all agents run independently.
    """

    name = "sparc_quick_scan"

    def build_agents(self, request: LLMRequest) -> List[BaseAgent]:
        """Build all 10 SPARC agents for parallel execution."""
        return [
            PlayerExperienceAgent(),
            ThemeAgent(),
            PurposeAgent(),
            GameplayAgent(),
            GoalsChallengesRewardsAgent(),
            PlaceAgent(),
            StoryNarrativeAgent(),
            UniqueFeaturesAgent(),
            ArtDirectionAgent(),
            OpportunitiesRisksAgent(),
        ]

    def _determine_status(self, score: int) -> str:
        """Determine status based on score."""
        if score >= 80:
            return "strong"
        elif score >= 60:
            return "adequate"
        elif score >= 40:
            return "weak"
        else:
            return "missing"

    def _determine_priority(self, score: int) -> str:
        """Determine improvement priority based on score."""
        if score < 40:
            return "critical"
        elif score < 60:
            return "high"
        elif score < 80:
            return "medium"
        else:
            return "low"

    def aggregate(
        self, agent_results: List[AgentResult], request: LLMRequest
    ) -> Dict[str, Any]:
        """
        Aggregate results from all 10 agents into a unified response.

        Args:
            agent_results: List of AgentResult objects from parallel execution
            request: Original LLM request

        Returns:
            Aggregated SPARCQuickScanResponse as dictionary
        """
        # Build map of agent name -> response data
        results_map = {}
        for agent_result in agent_results:
            if agent_result.success and agent_result.data:
                results_map[agent_result.agent_name] = agent_result.data

        # Calculate aspect scores with full metadata
        aspect_scores = []
        score_tuples = []  # For sorting

        for agent_name, response in results_map.items():
            # Response is a dictionary (from model_dump())
            if isinstance(response, dict) and "score" in response:
                score = response["score"]
                status = self._determine_status(score)
                priority = self._determine_priority(score)

                # Extract key issues
                key_issues = []
                if "issues" in response:
                    key_issues = response["issues"][:3]
                elif "missing_elements" in response:
                    key_issues = response["missing_elements"][:3]

                aspect_scores.append(
                    AspectScore(
                        aspect=agent_name,
                        score=score,
                        status=status,
                        key_issues=key_issues,
                        priority=priority,
                    )
                )
                score_tuples.append((agent_name, score))

        # Calculate overall readiness
        scores = [s.score for s in aspect_scores]
        readiness_score = round(sum(scores) / len(scores)) if scores else 0

        # Determine readiness status
        if readiness_score >= 80:
            readiness_status = "Ready"
        elif readiness_score >= 60:
            readiness_status = "Nearly Ready"
        elif readiness_score >= 40:
            readiness_status = "Needs Work"
        else:
            readiness_status = "Not Ready"

        # Find strongest and weakest aspects
        sorted_aspects = sorted(score_tuples, key=lambda x: x[1], reverse=True)
        strongest_aspects = [name for name, _ in sorted_aspects[:3]]
        weakest_aspects = [name for name, _ in sorted_aspects[-3:]]

        # Collect critical gaps (aspects with score < 40)
        critical_gaps = []
        for aspect_score in aspect_scores:
            if aspect_score.score < 40:
                critical_gaps.append(
                    f"{aspect_score.aspect}: {', '.join(aspect_score.key_issues)}"
                )

        # Estimate time to ready based on readiness score
        if readiness_score >= 80:
            estimated_time = "0-2 hours"
        elif readiness_score >= 60:
            estimated_time = "4-6 hours"
        elif readiness_score >= 40:
            estimated_time = "8-12 hours"
        else:
            estimated_time = "16+ hours"

        # Build next steps from weakest aspects
        next_steps = []
        for name, score in sorted_aspects[-5:]:
            aspect_data = results_map.get(name)
            if (
                aspect_data
                and isinstance(aspect_data, dict)
                and "suggestions" in aspect_data
            ):  # noqa: E501
                suggestions = aspect_data["suggestions"][:1]
                if suggestions:
                    next_steps.append(f"[{name}] {suggestions[0]}")

        # Build final response
        return SPARCQuickScanResponse(
            readiness_score=readiness_score,
            readiness_status=readiness_status,
            aspect_scores=aspect_scores,
            strongest_aspects=strongest_aspects,
            weakest_aspects=weakest_aspects,
            critical_gaps=critical_gaps,
            estimated_time_to_ready=estimated_time,
            next_steps=next_steps[:5],
            # Individual aspect results
            player_experience=results_map.get("player_experience"),
            theme=results_map.get("theme"),
            purpose=results_map.get("purpose"),
            gameplay=results_map.get("gameplay"),
            goals_challenges_rewards=results_map.get("goals_challenges_rewards"),
            place=results_map.get("place"),
            story_narrative=results_map.get("story_narrative"),
            unique_features=results_map.get("unique_features"),
            art_direction=results_map.get("art_direction"),
            opportunities_risks=results_map.get("opportunities_risks"),
        ).model_dump()


# Register workflow for agentic execution
register_workflow("sparc.quick_scan", SPARCQuickScanWorkflow)
