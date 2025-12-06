"""
SPARC V2 Router Graph.

Coordinates: Router → Parallel Aspect Agents → Synthesis
"""

import asyncio
import logging
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
from sparc.llm.agents.v2.document_context import DocumentContextAgent
from sparc.llm.schemas.v2.document_context import DocumentContextResponse
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
        user=None,
    ):
        """Initialize the graph."""
        self.model_manager = model_manager
        self.config = config
        self.event_collector = event_collector
        self.evaluation = evaluation
        self.user = user

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

        # Step 1: Run router, pillar context, and document context in parallel
        router_task = self._run_router(context, target_aspects)
        pillar_task = self._run_pillar_context(context, request.data)

        # Document task is optional
        document_file = request.data.get("document_file")

        if document_file:
            document_task = self._run_document_context(
                context, document_file, target_aspects
            )
            router_result, pillar_result, document_result = await asyncio.gather(
                router_task, pillar_task, document_task, return_exceptions=True
            )
        else:
            router_result, pillar_result = await asyncio.gather(
                router_task, pillar_task, return_exceptions=True
            )
            document_result = None

        # Handle router result
        if isinstance(router_result, Exception):
            errors.append(
                ErrorInfo(
                    code="ROUTER_EXCEPTION",
                    message=str(router_result),
                    severity="error",
                )
            )
            return self._build_error_result(errors, agent_results, start_time)

        # At this point, router_result is guaranteed to be AgentResult
        assert isinstance(router_result, AgentResult)
        agent_results.append(router_result)

        if not router_result.success:
            if router_result.error:
                errors.append(router_result.error)
            return self._build_error_result(errors, agent_results, start_time)

        if not router_result.data:
            return self._build_error_result(errors, agent_results, start_time)

        router_response = RouterResponse(**router_result.data)

        # Handle pillar context result
        pillar_context = None
        if isinstance(pillar_result, Exception):
            logger = logging.getLogger(__name__)
            logger.error(
                f"Pillar context task raised exception: "
                f"{type(pillar_result).__name__}: {pillar_result}",
                exc_info=True,
            )
        else:
            # At this point, pillar_result is guaranteed to be AgentResult
            assert isinstance(pillar_result, AgentResult)
            # Always add to agent_results for tracking
            agent_results.append(pillar_result)
            # Use pillar context if we have valid data
            # (even if success=False, data might be usable)
            if pillar_result.data and isinstance(pillar_result.data, dict):
                pillar_context = pillar_result.data

        # Handle document context result
        document_context = None
        if document_result is not None:
            if isinstance(document_result, Exception):

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Document context task raised exception: "
                    f"{type(document_result).__name__}: {document_result}",
                    exc_info=True,
                )
            else:
                # At this point, document_result is guaranteed to be AgentResult
                assert isinstance(document_result, AgentResult)
                agent_results.append(document_result)
                # Use document context if we have valid data
                if document_result.success and document_result.data:
                    try:
                        document_context = DocumentContextResponse(
                            **document_result.data
                        )
                    except Exception as e:

                        logger = logging.getLogger(__name__)
                        logger.error(
                            f"Failed to parse document context response: {e}",
                            exc_info=True,
                        )

        # Step 2: Run aspect agents in parallel
        aspect_results = await self._run_aspect_agents(
            context, router_response, target_aspects, pillar_context, document_context
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
            pillar_context=pillar_context,
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

    async def _run_pillar_context(
        self, context: Dict[str, Any], request_data: Dict[str, Any]
    ) -> AgentResult:
        """
        Run pillar context agent to prepare pillar information for aspect agents.

        Returns empty result if no pillars or pillar_mode is 'none'.
        """
        from asgiref.sync import sync_to_async

        from pillars.models import Pillar
        from pillars.views import format_pillars_text
        from sparc.llm.agents.v2.pillar_context import PillarContextAgent
        from sparc.llm.schemas.v2.pillar_context import PillarContextResponse

        pillar_mode = request_data.get("pillar_mode", "smart")

        try:
            agent = PillarContextAgent()
        except Exception as e:

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create agent: {e}", exc_info=True)
            raise

        try:

            def build_empty_response(mode: str) -> Dict[str, Any]:
                normalized = mode if mode in {"all", "smart", "none"} else "smart"
                return PillarContextResponse(
                    mode=normalized,
                    pillars_available=False,
                    all_pillars_text="",
                    smart_assignments={},
                    pillars_count=0,
                ).model_dump()

            def build_result(data: Dict[str, Any]) -> AgentResult:
                return AgentResult(
                    agent_name="pillar_context",
                    success=True,
                    data=data,
                    model_used=None,
                    execution_time_ms=0,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                )

            async def persist_result(
                input_payload: Dict[str, Any], agent_result: AgentResult
            ) -> None:
                if not self.evaluation:
                    return

                try:
                    await agent._save_result_async(
                        evaluation=self.evaluation,
                        input_data=input_payload,
                        result=agent_result,
                    )
                except Exception as e:

                    logger = logging.getLogger(__name__)
                    logger.error(
                        f"Failed to persist pillar result: {e}",
                        exc_info=True,
                    )
                    raise

            if pillar_mode == "none":
                result = build_result(build_empty_response("none"))
                await persist_result({"pillar_mode": pillar_mode}, result)
                return result

            # Resolve user either from explicit graph user or evaluation
            user = self.user
            if not user and self.evaluation and hasattr(self.evaluation, "user"):
                user = self.evaluation.user

            if not user or not getattr(user, "is_authenticated", False):
                result = build_result(build_empty_response(pillar_mode))
                await persist_result(
                    {"pillar_mode": pillar_mode, "has_user": False}, result
                )
                return result

            # Fetch pillars asynchronously
            @sync_to_async
            def get_user_pillars(user_obj):
                return list(Pillar.objects.filter(user=user_obj))

            pillars = await get_user_pillars(user)
            if not pillars:
                result = build_result(build_empty_response(pillar_mode))
                await persist_result(
                    {"pillar_mode": pillar_mode, "pillars_available": False}, result
                )
                return result

            pillars_text = format_pillars_text(pillars)

            if pillar_mode == "all":
                response = PillarContextResponse(
                    mode="all",
                    pillars_available=True,
                    all_pillars_text=pillars_text,
                    smart_assignments={},
                    pillars_count=len(pillars),
                ).model_dump()
                result = build_result(response)
                await persist_result(
                    {"pillar_mode": pillar_mode, "pillars_text": pillars_text}, result
                )
                return result

            # For "smart" mode, run agent to assign pillars to aspects
            if self.event_collector:
                self.event_collector.add_agent_started(agent.name)

            agent_context = {
                **context,
                "data": {
                    "pillars_text": pillars_text,
                    "mode": "smart",
                    "pillar_mode": pillar_mode,
                },
            }

            result = await agent.run(agent_context)

            if result.success and result.data:
                # Agent returns PillarAssignmentsResponse, construct full response
                assignments = result.data.get("smart_assignments", {})
                full_response = PillarContextResponse(
                    mode="smart",
                    pillars_available=True,
                    all_pillars_text=pillars_text,
                    smart_assignments=assignments,
                    pillars_count=len(pillars),
                )
                result.data = full_response.model_dump()

            if self.event_collector:
                self.event_collector.add_agent_finished(agent.name)

            await persist_result(agent_context["data"], result)

            return result
        except Exception as e:

            logger = logging.getLogger(__name__)
            logger.error(f"Exception in _run_pillar_context: {e}", exc_info=True)
            raise

    async def _run_document_context(
        self,
        context: Dict[str, Any],
        document_file: Dict[str, Any],
        target_aspects: List[str],
    ) -> AgentResult:
        """
        Run document context agent to extract aspect-relevant content from
        uploaded document.

        Args:
            context: Execution context
            document_file: Dict with file_path, file_type, original_name
            target_aspects: List of aspect names to extract for

        Returns:
            AgentResult with document extractions
        """
        logger = logging.getLogger(__name__)

        try:
            agent = DocumentContextAgent()

            if self.event_collector:
                self.event_collector.add_agent_started(agent.name)

            # Prepare agent context
            agent_context = {
                **context,
                "data": {
                    "file_path": document_file["file_path"],
                    "file_type": document_file.get("file_type", "pdf"),
                    "target_aspects": target_aspects,
                },
            }

            # Execute agent
            result = await agent.run(agent_context)

            # Save to DB if evaluation exists (save even if not successful,
            # like pillar context)
            if self.evaluation:
                try:
                    await agent._save_result_async(
                        evaluation=self.evaluation,
                        input_data=agent_context["data"],
                        result=result,
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to save document context result: {e}",
                        exc_info=True,
                    )

            if self.event_collector:
                self.event_collector.add_agent_finished(agent.name)

            return result

        except Exception as e:
            logger.error(
                f"Exception in _run_document_context: {e}",
                exc_info=True,
            )
            # Return error result instead of raising
            error_result = AgentResult(
                agent_name="document_context",
                success=False,
                data=None,
                error=ErrorInfo(
                    code="DOCUMENT_CONTEXT_ERROR",
                    message=str(e),
                    severity="error",
                ),
                execution_time_ms=0,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            )

            # Try to save error result to DB
            if self.evaluation:
                try:
                    agent = DocumentContextAgent()
                    await agent._save_result_async(
                        evaluation=self.evaluation,
                        input_data={
                            "file_path": document_file.get("file_path", "unknown")
                        },
                        result=error_result,
                    )
                    pass
                except Exception as save_error:
                    logger.error(
                        f"Failed to save error result: {save_error}",
                        exc_info=True,
                    )

            return error_result

    async def _run_aspect_agents(
        self,
        context: Dict[str, Any],
        router_response: RouterResponse,
        target_aspects: List[str],
        pillar_context: Optional[Dict[str, Any]] = None,
        document_context: Optional[DocumentContextResponse] = None,
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

            # Get document extraction for this aspect
            document_sections = []
            document_insights = []
            if document_context:
                for doc_extraction in document_context.extractions:
                    if doc_extraction.aspect_name == aspect_name:
                        document_sections = doc_extraction.extracted_sections
                        document_insights = doc_extraction.key_insights
                        break

            tasks.append(
                self._run_single_aspect(
                    context,
                    agent_class,
                    aspect_name,
                    sections,
                    semaphore,
                    pillar_context,
                    document_sections,
                    document_insights,
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
        pillar_context: Optional[Dict[str, Any]] = None,
        document_sections: Optional[List[str]] = None,
        document_insights: Optional[List[str]] = None,
    ) -> AgentResult:
        """Run a single aspect agent."""
        async with semaphore:
            agent = agent_class()

            if self.event_collector:
                self.event_collector.add_agent_started(agent.name)

            # Build agent data with extracted sections and optional pillar context
            agent_data: Dict[str, Any] = {"extracted_sections": sections}

            # Add document context if available (Option A: backward compatible)
            if document_sections:
                agent_data["document_sections"] = document_sections
            if document_insights:
                agent_data["document_insights"] = document_insights

            # Extract only relevant pillars for this aspect (if available)
            if pillar_context and isinstance(pillar_context, dict):
                mode = pillar_context.get("mode", "all")
                all_pillars_text = pillar_context.get("all_pillars_text", "")
                pillars_available = pillar_context.get("pillars_available", False)

                if pillars_available and all_pillars_text:
                    relevant_pillars_text = ""

                    if mode == "smart":
                        # Extract only pillars assigned to this aspect
                        smart_assignments = pillar_context.get("smart_assignments", {})
                        relevant_pillar_ids = smart_assignments.get(aspect_name, [])

                        if relevant_pillar_ids:
                            # Extract only relevant pillar lines
                            pillar_lines = all_pillars_text.split("\n")
                            relevant_pillars = []
                            for line in pillar_lines:
                                for pillar_id in relevant_pillar_ids:
                                    if line.startswith(f"[ID: {pillar_id}]"):
                                        relevant_pillars.append(line)
                                        break
                            relevant_pillars_text = "\n".join(relevant_pillars)
                    elif mode == "all":
                        # Use all pillars
                        relevant_pillars_text = all_pillars_text

                    # Only add pillar context if we have relevant pillars
                    if relevant_pillars_text:
                        agent_data["pillar_context"] = {
                            "mode": mode,
                            "pillars_available": True,
                            "pillars_text": relevant_pillars_text,
                            "pillars_count": len(relevant_pillars_text.split("\n")),
                        }

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
                # Run agent with extracted sections and pillar context
                agent_context = {
                    **context,
                    "data": agent_data,
                }
                result = await agent.run(agent_context)

            # Save to DB - use the full agent_data that was actually sent to the agent
            if self.evaluation:
                # Use agent_data directly - it already has the smart pillar context
                await agent._save_result_async(
                    evaluation=self.evaluation,
                    input_data=agent_data,
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
        pillar_context: Optional[Dict[str, Any]] = None,
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

        # Extract pillar metadata
        pillar_mode = None
        pillars_count = 0
        if pillar_context:
            pillar_mode = pillar_context.get("mode")
            pillars_count = pillar_context.get("pillars_count", 0)

        return SPARCV2Response(
            aspect_results=aspect_results,
            synthesis=synthesis,
            mode=mode,
            model_id=model_id,
            execution_time_ms=execution_time_ms,
            total_tokens=total_tokens,
            estimated_cost_eur=cost,
            agent_execution_details=agent_execution_details,
            pillar_mode=pillar_mode,
            pillars_count=pillars_count,
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
