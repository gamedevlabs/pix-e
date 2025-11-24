"""
SPARC V2 Router Graph.

Coordinates: Router → Parallel Aspect Agents → Synthesis
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Type

from llm.agent_registry import register_graph
from llm.config import Config
from llm.events import EventCollector
from llm.providers.manager import ModelManager
from llm.types import AgentResult, ErrorInfo, ExecutionResult, LLMRequest
from sparc.llm.agents.v2 import (
    ArtDirectionAgentV2,
    GameplayAgentV2,
    GoalsChallengesRewardsAgentV2,
    OpportunitiesRisksAgentV2,
    PlaceAgentV2,
    PlayerExperienceAgentV2,
    PurposeAgentV2,
    RouterAgent,
    StoryNarrativeAgentV2,
    SynthesisAgent,
    ThemeAgentV2,
    UniqueFeaturesAgentV2,
)
from sparc.llm.agents.v2.aspect_base import AspectAgentV2
from sparc.llm.schemas.v2.router import RouterResponse
from sparc.llm.schemas.v2.synthesis import SPARCV2Response
from sparc.models import SPARCEvaluation

# Map aspect names to agent classes
ASPECT_AGENTS: Dict[str, Type[AspectAgentV2]] = {
    "player_experience": PlayerExperienceAgentV2,
    "theme": ThemeAgentV2,
    "purpose": PurposeAgentV2,
    "gameplay": GameplayAgentV2,
    "goals_challenges_rewards": GoalsChallengesRewardsAgentV2,
    "place": PlaceAgentV2,
    "story_narrative": StoryNarrativeAgentV2,
    "unique_features": UniqueFeaturesAgentV2,
    "art_direction": ArtDirectionAgentV2,
    "opportunities_risks": OpportunitiesRisksAgentV2,
}


class SPARCRouterGraph:
    """
    V2 Router-based SPARC evaluation graph.

    Execution flow:
    1. Router extracts aspect-relevant content
    2. Aspect agents run in parallel on their extracted content
    3. Synthesis agent aggregates results

    Supports three modes:
    - full: All 10 aspects + synthesis
    - single: Router + 1 aspect (no synthesis)
    - multiple: Router + selected aspects (no synthesis)
    """

    name = "sparc_router_v2"

    def __init__(
        self,
        model_manager: ModelManager,
        config: Config,
        event_collector: Optional[EventCollector] = None,
        evaluation: Optional[SPARCEvaluation] = None,
    ):
        """Initialize the graph."""
        self.model_manager = model_manager
        self.config = config
        self.event_collector = event_collector
        self.evaluation = evaluation

    async def run(
        self,
        request: LLMRequest,
        mode: str = "full",
        target_aspects: Optional[List[str]] = None,
    ) -> ExecutionResult:
        """
        Execute the router-based evaluation.

        Args:
            request: LLM request with game_text in data
            mode: "full", "single", or "multiple"
            target_aspects: Aspects to evaluate (for single/multiple modes)
        """
        start_time = time.time()

        if self.event_collector:
            self.event_collector.add_run_started()

        # Determine target aspects
        if mode == "full" or target_aspects is None:
            target_aspects = list(ASPECT_AGENTS.keys())

        # Build base context
        context = {
            "model_manager": self.model_manager,
            "data": request.data,
        }
        if hasattr(request, "model_id") and request.model_id:
            context["model_id"] = request.model_id

        errors: List[ErrorInfo] = []
        agent_results: List[AgentResult] = []

        # Step 1: Run router
        router_result = await self._run_router(context, target_aspects)
        agent_results.append(router_result)

        if not router_result.success:
            if router_result.error:
                errors.append(router_result.error)
            return self._build_error_result(errors, agent_results, start_time)

        if not router_result.data:
            return self._build_error_result(errors, agent_results, start_time)

        router_response = RouterResponse(**router_result.data)

        # Step 2: Run aspect agents in parallel
        aspect_results = await self._run_aspect_agents(
            context, router_response, target_aspects
        )
        agent_results.extend(aspect_results)

        # Build aspect results dict
        aspect_data: Dict[str, Any] = {}
        for result in aspect_results:
            if result.success and result.data:
                aspect_name = result.data.get("aspect_name", result.agent_name)
                aspect_data[aspect_name] = result.data

        # Step 3: Run synthesis (only for full mode)
        synthesis_data = None
        if mode == "full":
            synthesis_result = await self._run_synthesis(context, aspect_data)
            agent_results.append(synthesis_result)
            if synthesis_result.success:
                synthesis_data = synthesis_result.data

        # Calculate totals
        total_time = int((time.time() - start_time) * 1000)
        total_tokens = sum(r.total_tokens for r in agent_results)

        # Build response
        model_id = context.get("model_id", "unknown")
        if not isinstance(model_id, str):
            model_id = "unknown"

        aggregated = self._build_response(
            mode=mode,
            aspect_results=aspect_data,
            synthesis=synthesis_data,
            model_id=model_id,
            execution_time_ms=total_time,
            total_tokens=total_tokens,
            agent_results=agent_results,
        )

        if self.event_collector:
            self.event_collector.add_run_completed(success=True)

        return ExecutionResult(
            success=True,
            agent_results=agent_results,
            aggregated_data=aggregated,
            total_execution_time_ms=total_time,
            errors=[],
            warnings=[],
        )

    async def _run_router(
        self, context: Dict[str, Any], target_aspects: List[str]
    ) -> AgentResult:
        """Run the router agent with retry."""
        router = RouterAgent()

        if self.event_collector:
            self.event_collector.add_agent_started(router.name)

        # Prepare router context
        router_context = {
            **context,
            "data": {
                **context["data"],
                "target_aspects": target_aspects,
            },
        }

        # Execute with retry
        result = await router.run_with_retry(router_context)

        # Save to DB if evaluation exists
        if self.evaluation and result.success:
            await router._save_result_async(
                evaluation=self.evaluation,
                input_data=router_context["data"],
                result=result,
            )

        if self.event_collector:
            self.event_collector.add_agent_finished(router.name)

        return result

    async def _run_aspect_agents(
        self,
        context: Dict[str, Any],
        router_response: RouterResponse,
        target_aspects: List[str],
    ) -> List[AgentResult]:
        """Run aspect agents in parallel."""
        max_parallel = getattr(self.config, "max_parallel_agents", 5)
        semaphore = asyncio.Semaphore(max_parallel)

        tasks = []
        for aspect_name in target_aspects:
            agent_class = ASPECT_AGENTS.get(aspect_name)
            if not agent_class:
                continue

            extraction = router_response.get_extraction(aspect_name)
            sections = extraction.extracted_sections if extraction else []

            tasks.append(
                self._run_single_aspect(
                    context, agent_class, aspect_name, sections, semaphore
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed: List[AgentResult] = []
        for r in results:
            if isinstance(r, Exception):
                processed.append(
                    AgentResult(
                        agent_name="unknown",
                        success=False,
                        data=None,
                        error=ErrorInfo(
                            code="AGENT_EXCEPTION",
                            message=str(r),
                            severity="error",
                        ),
                        execution_time_ms=0,
                    )
                )
            elif isinstance(r, AgentResult):
                processed.append(r)

        return processed

    async def _run_single_aspect(
        self,
        context: Dict[str, Any],
        agent_class: Type[AspectAgentV2],
        aspect_name: str,
        sections: List[str],
        semaphore: asyncio.Semaphore,
    ) -> AgentResult:
        """Run a single aspect agent."""
        async with semaphore:
            agent = agent_class()

            if self.event_collector:
                self.event_collector.add_agent_started(agent.name)

            # Check if we should skip LLM call
            if len(sections) == 0:
                # Return not_provided without LLM call
                response = agent.get_not_provided_response()
                result = AgentResult(
                    agent_name=agent.name,
                    success=True,
                    data=response.model_dump(),
                    model_used=None,
                    execution_time_ms=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                )
            else:
                # Run agent with extracted sections
                agent_context = {
                    **context,
                    "data": {"extracted_sections": sections},
                }
                result = await agent.run(agent_context)

            # Save to DB
            if self.evaluation:
                await agent._save_result_async(
                    evaluation=self.evaluation,
                    input_data={"extracted_sections": sections},
                    result=result,
                )

            if self.event_collector:
                self.event_collector.add_agent_finished(agent.name)

            return result

    async def _run_synthesis(
        self, context: Dict[str, Any], aspect_results: Dict[str, Any]
    ) -> AgentResult:
        """Run the synthesis agent."""
        synthesis = SynthesisAgent()

        if self.event_collector:
            self.event_collector.add_agent_started(synthesis.name)

        synthesis_context = {
            **context,
            "data": {"aspect_results": aspect_results},
        }

        result = await synthesis.run(synthesis_context)

        # Save to DB
        if self.evaluation:
            await synthesis._save_result_async(
                evaluation=self.evaluation,
                input_data={"aspect_results": aspect_results},
                result=result,
            )

        if self.event_collector:
            self.event_collector.add_agent_finished(synthesis.name)

        return result

    def _build_response(
        self,
        mode: str,
        aspect_results: Dict[str, Any],
        synthesis: Optional[Dict[str, Any]],
        model_id: str,
        execution_time_ms: int,
        total_tokens: int,
        agent_results: List[AgentResult],
    ) -> Dict[str, Any]:
        """Build the final response."""
        from sparc.llm.agents.v2.base import calculate_cost_eur
        from sparc.llm.schemas.v2.synthesis import AgentExecutionDetail

        cost = calculate_cost_eur(model_id, total_tokens // 2, total_tokens // 2)

        # Build agent execution details
        agent_execution_details = [
            AgentExecutionDetail(
                agent_name=result.agent_name,
                execution_time_ms=result.execution_time_ms,
                total_tokens=result.total_tokens,
                prompt_tokens=result.prompt_tokens or 0,
                completion_tokens=result.completion_tokens or 0,
                success=result.success,
            )
            for result in agent_results
        ]

        return SPARCV2Response(
            aspect_results=aspect_results,
            synthesis=synthesis,
            mode=mode,
            model_id=model_id,
            execution_time_ms=execution_time_ms,
            total_tokens=total_tokens,
            estimated_cost_eur=cost,
            agent_execution_details=agent_execution_details,
        ).model_dump()

    def _build_error_result(
        self,
        errors: List[ErrorInfo],
        agent_results: List[AgentResult],
        start_time: float,
    ) -> ExecutionResult:
        """Build error result."""
        total_time = int((time.time() - start_time) * 1000)

        if self.event_collector:
            self.event_collector.add_run_completed(success=False)

        return ExecutionResult(
            success=False,
            agent_results=agent_results,
            aggregated_data={},
            total_execution_time_ms=total_time,
            errors=errors,
            warnings=[],
        )


# Register graph
register_graph("sparc.router_v2", SPARCRouterGraph)
