"""
Pillar evaluation agent workflows.

Agent workflows coordinate multiple agents to complete complex operations
through parallel execution and result aggregation.
"""

import asyncio
from typing import Any, Dict, List

from llm.agent_registry import register_workflow
from llm.agent_runtime import BaseAgent
from llm.agent_workflow import BaseAgentWorkflow
from llm.logfire_config import get_logfire
from llm.types import LLMRequest
from pillars.llm.agents import (
    ConceptFitAgent,
    ContradictionResolutionAgent,
    ContradictionsAgent,
    SuggestAdditionsAgent,
    SynthesisAgent,
)


class PillarsEvaluationWorkflow(BaseAgentWorkflow):
    """
    Agent workflow for comprehensive pillar evaluation with conditional execution.

    Execution flow:
    1. Run ConceptFitAgent and ContradictionsAgent in parallel (detection phase)
    2. If gaps found: run SuggestAdditionsAgent with concept fit context
    3. If contradictions found: run ContradictionResolutionAgent with context

    Results are aggregated into a unified evaluation response.
    """

    def build_agents(self, request: LLMRequest) -> List[BaseAgent]:
        """
        Build list of detection agents for initial parallel execution.

        Note: Resolution agents are created dynamically based on detection results.
        """
        return [
            ConceptFitAgent(),
            ContradictionsAgent(),
        ]

    async def run(self, request: LLMRequest) -> Any:
        """
        Execute pillar evaluation with conditional resolution agents.

        Overrides base run() to implement conditional execution:
        1. Run detection agents in parallel
        2. Based on results, conditionally run resolution agents
        """
        from llm.types import AgentResult, ErrorInfo, ExecutionResult, WarningInfo

        logfire = get_logfire()

        # Wrap entire workflow in a parent span
        with logfire.span(
            "pillars.evaluate_all",
            workflow="PillarsEvaluationWorkflow",
            operation="evaluate_all",
        ):
            start_time = asyncio.get_event_loop().time()
            all_agent_results: List[AgentResult] = []
            errors: List[ErrorInfo] = []
            warnings: List[WarningInfo] = []

            # Phase 1: Run detection agents in parallel
            detection_agents = self.build_agents(request)
            detection_results = await self._run_agents_parallel(
                detection_agents, request.data, request
            )
            all_agent_results.extend(detection_results)

            # Extract detection results
            concept_fit_result = None
            contradictions_result = None

            for result in detection_results:
                if result.agent_name == "concept_fit":
                    concept_fit_result = result
                elif result.agent_name == "contradictions":
                    contradictions_result = result

            # Phase 2: Conditional resolution agents
            resolution_tasks: List[tuple[str, BaseAgent, Dict[str, Any]]] = []

            # Check if we need to suggest additions (gaps found)
            if concept_fit_result and concept_fit_result.success:
                has_gaps = concept_fit_result.data.get("hasGaps", False)
                missing_aspects = concept_fit_result.data.get("missingAspects", [])

                if has_gaps or missing_aspects:
                    # Create additions agent with concept fit context
                    additions_agent = SuggestAdditionsAgent()
                    additions_data = {
                        **request.data,
                        "concept_fit_feedback": concept_fit_result.data,
                    }
                    resolution_tasks.append(
                        ("additions", additions_agent, additions_data)
                    )

            # Check if we need to resolve contradictions
            if contradictions_result and contradictions_result.success:
                has_contradictions = contradictions_result.data.get(
                    "hasContradictions", False
                )
                contradictions_list = contradictions_result.data.get(
                    "contradictions", []
                )

                if has_contradictions and contradictions_list:
                    # Create resolution agent with contradictions context
                    resolution_agent = ContradictionResolutionAgent()
                    resolution_data = {
                        **request.data,
                        "contradictions_feedback": contradictions_result.data,
                    }
                    resolution_tasks.append(
                        ("resolution", resolution_agent, resolution_data)
                    )

            # Run resolution agents in parallel (if any)
            if resolution_tasks:
                resolution_agents = [
                    (name, agent) for name, agent, _ in resolution_tasks
                ]
                resolution_data_list = [data for _, _, data in resolution_tasks]

                # Run resolution agents
                resolution_coroutines = []
                for (name, agent), data in zip(resolution_agents, resolution_data_list):
                    context = {
                        "model_manager": self.model_manager,
                        "data": data,
                        "model_id": getattr(request, "model_id", None),
                        "model_preference": getattr(
                            request, "model_preference", "auto"
                        ),
                    }
                    resolution_coroutines.append(agent.run(context))

                resolution_results = await asyncio.gather(
                    *resolution_coroutines, return_exceptions=True
                )

                for result in resolution_results:
                    if isinstance(result, BaseException):
                        errors.append(
                            ErrorInfo(
                                code="AGENT_ERROR",
                                message=str(result),
                                severity="error",
                            )
                        )
                    elif isinstance(result, AgentResult):
                        all_agent_results.append(result)

            # Phase 3: Run synthesis agent to produce overall score
            # Collect results for synthesis
            additions_result = None
            for result in all_agent_results:
                if result.agent_name == "suggest_additions":
                    additions_result = result
                    break

            synthesis_agent = SynthesisAgent()
            synthesis_data = {
                **request.data,
                "concept_fit_result": (
                    concept_fit_result.data if concept_fit_result else {}
                ),
                "contradictions_result": (
                    contradictions_result.data if contradictions_result else {}
                ),
                "additions_result": (additions_result.data if additions_result else {}),
            }
            synthesis_context = {
                "model_manager": self.model_manager,
                "data": synthesis_data,
                "model_id": getattr(request, "model_id", None),
                "model_preference": getattr(request, "model_preference", "auto"),
            }

            try:
                synthesis_result = await synthesis_agent.run(synthesis_context)
                if isinstance(synthesis_result, AgentResult):
                    all_agent_results.append(synthesis_result)
            except Exception as e:
                errors.append(
                    ErrorInfo(
                        code="SYNTHESIS_ERROR",
                        message=str(e),
                        severity="error",
                    )
                )

            # Calculate total execution time
            end_time = asyncio.get_event_loop().time()
            total_time_ms = int((end_time - start_time) * 1000)

            # Aggregate results
            aggregated = self.aggregate(all_agent_results, request)

            return ExecutionResult(
                success=all(r.success for r in all_agent_results if r),
                agent_results=all_agent_results,
                aggregated_data=aggregated,
                total_execution_time_ms=total_time_ms,
                errors=errors,
                warnings=warnings,
            )

    async def _run_agents_parallel(
        self, agents: List[BaseAgent], data: Dict[str, Any], request: LLMRequest
    ) -> List[Any]:
        """Run a list of agents in parallel and return their results."""
        from llm.types import AgentResult

        coroutines = []
        for agent in agents:
            context = {
                "model_manager": self.model_manager,
                "data": data,
                "model_id": getattr(request, "model_id", None),
                "model_preference": getattr(request, "model_preference", "auto"),
            }
            coroutines.append(agent.run(context))

        results = await asyncio.gather(*coroutines, return_exceptions=True)

        # Convert exceptions to failed AgentResults
        processed_results: List[AgentResult] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                processed_results.append(
                    AgentResult(
                        agent_name=agents[i].name,
                        success=False,
                        data={},
                        model_used="",
                        execution_time_ms=0,
                        error=str(result),
                    )
                )
            elif isinstance(result, AgentResult):
                processed_results.append(result)

        return processed_results

    def aggregate(
        self, agent_results: List[Any], request: LLMRequest
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents into unified response.

        Returns a structure with:
        - concept_fit: ConceptFitAgent results
        - contradictions: ContradictionsAgent results
        - additions: SuggestAdditionsAgent results (if run)
        - resolution: ContradictionResolutionAgent results (if run)
        """
        aggregated = {
            "concept_fit": None,
            "contradictions": None,
            "additions": None,
            "resolution": None,
            "synthesis": None,
        }

        for agent_result in agent_results:
            if not agent_result.success or not agent_result.data:
                continue

            agent_name = agent_result.agent_name
            data = agent_result.data

            if agent_name == "concept_fit":
                aggregated["concept_fit"] = data
            elif agent_name == "contradictions":
                aggregated["contradictions"] = data
            elif agent_name == "suggest_additions":
                aggregated["additions"] = data
            elif agent_name == "contradiction_resolution":
                aggregated["resolution"] = data
            elif agent_name == "synthesis":
                aggregated["synthesis"] = data

        return aggregated


# Register workflow for the evaluate_all operation
register_workflow("pillars.evaluate_all", PillarsEvaluationWorkflow)
