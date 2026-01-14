"""
SPARC V2 Router Workflow.

Coordinates: Router → Parallel Aspect Agents → Synthesis
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Type

from llm.agent_registry import register_workflow
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

logger = logging.getLogger(__name__)

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


class SPARCRouterWorkflow:
    """
    V2 Router-based SPARC evaluation workflow.

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
        """Initialize the workflow."""
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

        target_aspects = self._resolve_target_aspects(mode, target_aspects)
        context = self._build_context(request)

        errors: List[ErrorInfo] = []
        agent_results: List[AgentResult] = []

        (
            router_response,
            pillar_context,
            document_context,
            preprocessing_results,
            preprocessing_errors,
        ) = await self._run_preprocessing(
            context=context,
            request_data=request.data,
            target_aspects=target_aspects,
        )
        agent_results.extend(preprocessing_results)
        errors.extend(preprocessing_errors)
        if errors:
            return self._build_error_result(errors, agent_results, start_time)

        if not router_response:
            errors.append(
                ErrorInfo(
                    code="ROUTER_MISSING",
                    message="Router response is required for v2 evaluation",
                    severity="error",
                )
            )
            return self._build_error_result(errors, agent_results, start_time)

        aspect_contexts = self._build_aspect_contexts_from_router(
            router_response, target_aspects
        )

        # Step 2: Run aspect agents in parallel
        aspect_results = await self._run_aspect_agents(
            context,
            aspect_contexts,
            target_aspects,
            pillar_context,
            document_context,
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

    def _resolve_target_aspects(
        self, mode: str, target_aspects: Optional[List[str]]
    ) -> List[str]:
        if mode == "full" or target_aspects is None:
            return list(ASPECT_AGENTS.keys())
        return target_aspects

    def _build_context(self, request: LLMRequest) -> Dict[str, Any]:
        context = {
            "model_manager": self.model_manager,
            "data": request.data,
        }
        if hasattr(request, "model_id") and request.model_id:
            context["model_id"] = request.model_id
        return context

    async def _run_preprocessing(
        self,
        *,
        context: Dict[str, Any],
        request_data: Dict[str, Any],
        target_aspects: List[str],
    ) -> tuple[
        Optional[RouterResponse],
        Optional[Dict[str, Any]],
        Optional[DocumentContextResponse],
        List[AgentResult],
        List[ErrorInfo],
    ]:
        errors: List[ErrorInfo] = []
        agent_results: List[AgentResult] = []

        router_task = self._run_router(context, target_aspects)
        pillar_task = self._run_pillar_context(context, request_data)

        document_file = request_data.get("document_file")
        tasks = [pillar_task]
        if router_task:
            tasks.insert(0, router_task)
        if document_file:
            tasks.append(
                self._run_document_context(context, document_file, target_aspects)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        router_result = None
        pillar_result = None
        document_result = None

        if router_task:
            router_result = results[0]
            pillar_result = results[1]
            if document_file:
                document_result = results[2]
        else:
            pillar_result = results[0]
            if document_file:
                document_result = results[1]

        router_response = self._parse_router_result(
            router_result, agent_results, errors
        )
        pillar_context = self._parse_pillar_result(pillar_result, agent_results)
        document_context = self._parse_document_result(document_result, agent_results)

        return (
            router_response,
            pillar_context,
            document_context,
            agent_results,
            errors,
        )

    def _parse_router_result(
        self,
        router_result: Any,
        agent_results: List[AgentResult],
        errors: List[ErrorInfo],
    ) -> Optional[RouterResponse]:
        if router_result is None:
            return None
        if isinstance(router_result, Exception):
            errors.append(
                ErrorInfo(
                    code="ROUTER_EXCEPTION",
                    message=str(router_result),
                    severity="error",
                )
            )
            return None
        assert isinstance(router_result, AgentResult)
        agent_results.append(router_result)
        if not router_result.success:
            if router_result.error:
                errors.append(router_result.error)
            return None
        if not router_result.data:
            errors.append(
                ErrorInfo(
                    code="ROUTER_EMPTY",
                    message="Router returned no data",
                    severity="error",
                )
            )
            return None
        return RouterResponse(**router_result.data)

    def _build_aspect_contexts_from_router(
        self, router_response: RouterResponse, target_aspects: List[str]
    ) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {aspect: [] for aspect in target_aspects}
        for extraction in router_response.extractions:
            if extraction.aspect_name in mapping:
                mapping[extraction.aspect_name] = extraction.extracted_sections
        return mapping

    def _parse_pillar_result(
        self, pillar_result: Any, agent_results: List[AgentResult]
    ) -> Optional[Dict[str, Any]]:
        if isinstance(pillar_result, Exception):
            logger.error(
                "Pillar context task raised exception: %s: %s",
                type(pillar_result).__name__,
                pillar_result,
                exc_info=True,
            )
            return None
        assert isinstance(pillar_result, AgentResult)
        agent_results.append(pillar_result)
        if pillar_result.data and isinstance(pillar_result.data, dict):
            return pillar_result.data
        return None

    def _parse_document_result(
        self, document_result: Any, agent_results: List[AgentResult]
    ) -> Optional[DocumentContextResponse]:
        if document_result is None:
            return None
        if isinstance(document_result, Exception):
            logger = logging.getLogger(__name__)
            logger.error(
                "Document context task raised exception: %s: %s",
                type(document_result).__name__,
                document_result,
                exc_info=True,
            )
            return None
        assert isinstance(document_result, AgentResult)
        agent_results.append(document_result)
        if document_result.success and document_result.data:
            try:
                return DocumentContextResponse(**document_result.data)
            except Exception as e:
                logger.error(
                    "Failed to parse document context response: %s",
                    e,
                    exc_info=True,
                )
        return None

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
        from pillars.utils import format_pillars_text
        from sparc.llm.agents.v2.pillar_context import PillarContextAgent
        from sparc.llm.schemas.v2.pillar_context import PillarContextResponse

        pillar_mode = request_data.get("pillar_mode", "smart")
        project_id = request_data.get("project_id")

        try:
            agent = PillarContextAgent()
        except Exception as e:
            logger.error("Failed to create agent: %s", e, exc_info=True)
            raise

        try:
            if pillar_mode == "none":
                result = self._build_pillar_result(
                    self._build_empty_pillar_response("none", PillarContextResponse)
                )
                await self._persist_agent_result(
                    agent, {"pillar_mode": pillar_mode}, result, "pillar result"
                )
                return result

            # Resolve user either from explicit workflow user or evaluation
            user = self.user
            if not user and self.evaluation and hasattr(self.evaluation, "user"):
                user = self.evaluation.user

            if not user or not getattr(user, "is_authenticated", False):
                result = self._build_pillar_result(
                    self._build_empty_pillar_response(
                        pillar_mode, PillarContextResponse
                    )
                )
                await self._persist_agent_result(
                    agent,
                    {"pillar_mode": pillar_mode, "has_user": False},
                    result,
                    "pillar result",
                )
                return result

            # Resolve project if not explicitly provided
            if not project_id:
                from game_concept.utils import get_current_project

                project = get_current_project(user)
                project_id = project.id if project else None

            # Fetch pillars asynchronously
            @sync_to_async
            def get_user_pillars(user_obj):
                qs = Pillar.objects.filter(user=user_obj)
                if project_id:
                    qs = qs.filter(project_id=project_id)
                return list(qs)

            pillars = await get_user_pillars(user)
            if not pillars:
                result = self._build_pillar_result(
                    self._build_empty_pillar_response(
                        pillar_mode, PillarContextResponse
                    )
                )
                await self._persist_agent_result(
                    agent,
                    {"pillar_mode": pillar_mode, "pillars_available": False},
                    result,
                    "pillar result",
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
                result = self._build_pillar_result(response)
                await self._persist_agent_result(
                    agent,
                    {"pillar_mode": pillar_mode, "pillars_text": pillars_text},
                    result,
                    "pillar result",
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

            await self._persist_agent_result(
                agent, agent_context["data"], result, "pillar result"
            )

            return result
        except Exception as e:
            logger.error("Exception in _run_pillar_context: %s", e, exc_info=True)
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
                        "Failed to save document context result: %s",
                        e,
                        exc_info=True,
                    )

            if self.event_collector:
                self.event_collector.add_agent_finished(agent.name)

            return result

        except Exception as e:
            logger.error("Exception in _run_document_context: %s", e, exc_info=True)
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
                        "Failed to save error result: %s",
                        save_error,
                        exc_info=True,
                    )

            return error_result

    async def _run_aspect_agents(
        self,
        context: Dict[str, Any],
        aspect_contexts: Dict[str, List[str]],
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

            sections = aspect_contexts.get(aspect_name, [])

            document_sections, document_insights = (
                self._get_document_context_for_aspect(document_context, aspect_name)
            )

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
            pillar_context_payload = self._build_pillar_context_for_aspect(
                pillar_context, aspect_name
            )
            if pillar_context_payload:
                agent_data["pillar_context"] = pillar_context_payload

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
        from sparc.llm.schemas.v2.synthesis import AgentExecutionDetail

        cost = 0

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

    def _build_empty_pillar_response(
        self, mode: str, response_schema: Type[Any]
    ) -> Dict[str, Any]:
        normalized = mode if mode in {"all", "smart", "none"} else "smart"
        return response_schema(
            mode=normalized,
            pillars_available=False,
            all_pillars_text="",
            smart_assignments={},
            pillars_count=0,
        ).model_dump()

    def _build_pillar_result(self, data: Dict[str, Any]) -> AgentResult:
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

    async def _persist_agent_result(
        self,
        agent: Any,
        input_payload: Dict[str, Any],
        agent_result: AgentResult,
        label: str,
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
            logger.error("Failed to persist %s: %s", label, e, exc_info=True)
            raise

    def _build_pillar_context_for_aspect(
        self, pillar_context: Optional[Dict[str, Any]], aspect_name: str
    ) -> Optional[Dict[str, Any]]:
        if not pillar_context or not isinstance(pillar_context, dict):
            return None

        mode = pillar_context.get("mode", "all")
        all_pillars_text = pillar_context.get("all_pillars_text", "")
        pillars_available = pillar_context.get("pillars_available", False)
        if not (pillars_available and all_pillars_text):
            return None

        if mode == "smart":
            smart_assignments = pillar_context.get("smart_assignments", {})
            relevant_pillar_ids = smart_assignments.get(aspect_name, [])
            if not relevant_pillar_ids:
                return None
            relevant_pillars = [
                line
                for line in all_pillars_text.split("\n")
                for pillar_id in relevant_pillar_ids
                if line.startswith(f"[ID: {pillar_id}]")
            ]
            relevant_pillars_text = "\n".join(dict.fromkeys(relevant_pillars))
        elif mode == "all":
            relevant_pillars_text = all_pillars_text
        else:
            return None

        if not relevant_pillars_text:
            return None

        return {
            "mode": mode,
            "pillars_available": True,
            "pillars_text": relevant_pillars_text,
            "pillars_count": len(relevant_pillars_text.split("\n")),
        }

    def _get_document_context_for_aspect(
        self,
        document_context: Optional[DocumentContextResponse],
        aspect_name: str,
    ) -> tuple[List[str], List[str]]:
        if not document_context:
            return [], []
        for doc_extraction in document_context.extractions:
            if doc_extraction.aspect_name == aspect_name:
                return doc_extraction.extracted_sections, doc_extraction.key_insights
        return [], []


# Register workflow
register_workflow("sparc.router_v2", SPARCRouterWorkflow)
