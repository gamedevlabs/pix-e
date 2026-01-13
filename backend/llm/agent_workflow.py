"""
Agent Workflow for Parallel Agent Execution

Provides BaseAgentWorkflow class that coordinates multiple agents running in parallel.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from llm.agent_runtime import BaseAgent
from llm.config import Config
from llm.events import EventCollector
from llm.logfire_config import get_logfire
from llm.providers.manager import ModelManager
from llm.types import AgentResult, ErrorInfo, ExecutionResult, LLMRequest, WarningInfo


class BaseAgentWorkflow(ABC):
    """
    Base class for agent workflows.

    An agent workflow coordinates multiple agents to complete a complex operation:
    1. Builds list of agents to execute
    2. Runs agents in parallel (with concurrency limit)
    3. Emits events for observability
    4. Aggregates results into final output

    Subclasses must implement:
    - build_agents(): Create list of agents for this operation
    - aggregate(): Combine agent results into final output
    """

    def __init__(
        self,
        model_manager: ModelManager,
        config: Config,
        event_collector: EventCollector | None = None,
    ):
        """
        Initialize agent workflow.

        Args:
            model_manager: ModelManager for LLM calls
            config: Configuration with max_parallel_agents
            event_collector: Optional EventCollector for tracking events
        """
        self.model_manager = model_manager
        self.config = config
        self.event_collector = event_collector

    @abstractmethod
    def build_agents(self, request: LLMRequest) -> List[BaseAgent]:
        """
        Build list of agents to execute for this request.

        Args:
            request: The LLM request
        """
        pass

    @abstractmethod
    def aggregate(
        self, agent_results: List[Any], request: LLMRequest
    ) -> Dict[str, Any]:
        """
        Aggregate agent results into final output.

        Args:
            agent_results: List of AgentResult objects
            request: Original request
        """
        pass

    async def _run_agent(
        self, agent: BaseAgent, context: Dict[str, Any], semaphore: asyncio.Semaphore
    ) -> Any:
        """Run single agent with event tracking and semaphore."""
        logfire = get_logfire()

        async with semaphore:
            # Create span for individual agent execution
            with logfire.span(
                f"agent.{agent.name}",
                agent_name=agent.name,
                model=context.get("model_id", "auto"),
            ):
                if self.event_collector:
                    self.event_collector.add_agent_started(agent.name)

                result = await agent.run(context)

                if self.event_collector:
                    self.event_collector.add_agent_finished(agent.name)

                # Log agent result details
                if result.success:
                    logfire.info(
                        f"agent.{agent.name}.completed",
                        success=True,
                        execution_time_ms=result.execution_time_ms,
                        model_used=result.model_used,
                        prompt_tokens=result.prompt_tokens,
                        completion_tokens=result.completion_tokens,
                        total_tokens=result.total_tokens,
                    )
                else:
                    logfire.warn(
                        f"agent.{agent.name}.failed",
                        success=False,
                        error=str(result.error) if result.error else None,
                    )

                return result

    def _build_context(self, request: LLMRequest) -> Dict[str, Any]:
        context = {
            "model_manager": self.model_manager,
            "data": request.data,
            "model_preference": getattr(request, "model_preference", "auto"),
        }
        if hasattr(request, "model_id") and request.model_id:
            context["model_id"] = request.model_id
        return context

    def _get_max_parallel(self) -> int:
        return getattr(self.config, "max_parallel_agents", 3)

    async def _run_agents(
        self, agents: List[BaseAgent], context: Dict[str, Any]
    ) -> List[Any]:
        semaphore = asyncio.Semaphore(self._get_max_parallel())
        tasks = [self._run_agent(agent, context, semaphore) for agent in agents]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _process_agent_results(
        self, agent_results: List[Any]
    ) -> tuple[
        List[AgentResult], List[AgentResult], List[ErrorInfo], List[WarningInfo]
    ]:
        successful_results: List[AgentResult] = []
        errors: List[ErrorInfo] = []
        warnings: List[WarningInfo] = []
        valid_agent_results: List[AgentResult] = []

        for result in agent_results:
            if isinstance(result, Exception):
                errors.append(
                    ErrorInfo(
                        code="AGENT_EXCEPTION",
                        message=str(result),
                        severity="error",
                        diagnostics=None,
                    )
                )
                continue

            if not isinstance(result, AgentResult):
                continue

            valid_agent_results.append(result)
            if not result.success:
                warnings.append(
                    WarningInfo(
                        code="AGENT_FAILURE",
                        message=f"Agent {result.agent_name} failed",
                        context={
                            "agent": result.agent_name,
                            "error": str(result.error),
                        },
                    )
                )
            successful_results.append(result)

        return valid_agent_results, successful_results, errors, warnings

    def _aggregate_results(
        self, successful_results: List[AgentResult], request: LLMRequest
    ) -> tuple[Dict[str, Any], List[ErrorInfo]]:
        errors: List[ErrorInfo] = []
        try:
            aggregated_data = self.aggregate(successful_results, request)
        except Exception as e:
            errors.append(
                ErrorInfo(
                    code="AGGREGATION_ERROR",
                    message=f"Aggregation failed: {str(e)}",
                    severity="error",
                    diagnostics=None,
                )
            )
            aggregated_data = {}
        return aggregated_data, errors

    async def run(self, request: LLMRequest) -> ExecutionResult:
        """
        Execute the agent workflow with parallel agents.

        Args:
            request: The LLM request
        """
        logfire = get_logfire()

        # Build agents first to get count
        agents = self.build_agents(request)

        with logfire.span(
            "agent_workflow.execute",
            workflow_name=getattr(self, "name", self.__class__.__name__),
            num_agents=len(agents),
            max_parallel=self._get_max_parallel(),
        ):
            start_time = time.time()

            if self.event_collector:
                self.event_collector.add_run_started()

            context = self._build_context(request)
            agent_results = await self._run_agents(agents, context)
            (
                valid_agent_results,
                successful_results,
                errors,
                warnings,
            ) = self._process_agent_results(agent_results)

            # Calculate execution time
            total_execution_time_ms = int((time.time() - start_time) * 1000)

            # If all agents failed, this is an error
            if not successful_results and errors:
                if self.event_collector:
                    self.event_collector.add_run_completed(success=False)

                return ExecutionResult(
                    success=False,
                    agent_results=valid_agent_results,
                    aggregated_data={},
                    total_execution_time_ms=total_execution_time_ms,
                    errors=errors,
                    warnings=warnings,
                )

            # Aggregate results
            aggregated_data, aggregation_errors = self._aggregate_results(
                successful_results, request
            )
            errors.extend(aggregation_errors)

            # Emit run completed event
            if self.event_collector:
                self.event_collector.add_run_completed(success=len(errors) == 0)

            return ExecutionResult(
                success=len(errors) == 0,
                agent_results=valid_agent_results,
                aggregated_data=aggregated_data,
                total_execution_time_ms=total_execution_time_ms,
                errors=errors,
                warnings=warnings,
            )
