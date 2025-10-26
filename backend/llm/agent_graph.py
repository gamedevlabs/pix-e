"""
Agent Graph for Parallel Agent Execution

Provides BaseAgentGraph class that coordinates multiple agents running in parallel.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from llm.agent_runtime import BaseAgent
from llm.config import Config
from llm.events import EventCollector
from llm.providers.manager import ModelManager
from llm.types import AgentResult, ErrorInfo, ExecutionResult, LLMRequest, WarningInfo


class BaseAgentGraph(ABC):
    """
    Base class for agent graphs.

    An agent graph coordinates multiple agents to complete a complex operation:
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
        Initialize agent graph.

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
        async with semaphore:
            if self.event_collector:
                self.event_collector.add_agent_started(agent.name)

            result = await agent.run(context)

            if self.event_collector:
                self.event_collector.add_agent_finished(agent.name)

            return result

    async def run(self, request: LLMRequest) -> ExecutionResult:
        """
        Execute the agent graph with parallel agents.

        Args:
            request: The LLM request
        """
        start_time = time.time()

        if self.event_collector:
            self.event_collector.add_run_started()

        # Build agents and execution context
        agents = self.build_agents(request)
        context = {
            "model_manager": self.model_manager,
            "data": request.data,
            "model_preference": getattr(request, "model_preference", "auto"),
        }

        # Pass explicit model_id if provided
        if hasattr(request, "model_id") and request.model_id:
            context["model_id"] = request.model_id

        # Execute agents in parallel with concurrency limit
        max_parallel = getattr(self.config, "max_parallel_agents", 3)
        semaphore = asyncio.Semaphore(max_parallel)
        tasks = [self._run_agent(agent, context, semaphore) for agent in agents]
        agent_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful results from errors
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
            elif isinstance(result, AgentResult):
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
                # Include all agent results
                successful_results.append(result)

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
