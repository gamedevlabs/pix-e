"""
Pillar evaluation agent graphs.

Agent graphs coordinate multiple agents to complete complex operations
through parallel execution and result aggregation.
"""

from typing import Any, Dict, List

from llm.agent_graph import BaseAgentGraph
from llm.agent_registry import register_graph
from llm.agent_runtime import BaseAgent
from llm.types import LLMRequest
from pillars.llm.agents import (
    EvaluateCompletenessAgent,
    EvaluateContradictionsAgent,
    SuggestAdditionsAgent,
)


class PillarsEvaluationGraph(BaseAgentGraph):
    """
    Agent graph for comprehensive pillar evaluation.

    Coordinates three agents running in parallel:
    - EvaluateCompletenessAgent: Checks design coverage
    - EvaluateContradictionsAgent: Finds conflicts
    - SuggestAdditionsAgent: Suggests improvements

    Results are aggregated into a unified evaluation response.
    """

    def build_agents(self, request: LLMRequest) -> List[BaseAgent]:
        """
        Build list of agents for parallel execution.

        Args:
            request: The LLM request
        """
        return [
            EvaluateCompletenessAgent(),
            EvaluateContradictionsAgent(),
            SuggestAdditionsAgent(),
        ]

    def aggregate(
        self, agent_results: List[Any], request: LLMRequest
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents into unified response.

        Args:
            agent_results: List of AgentResult objects from agents
            request: Original request
        """
        aggregated = {
            "completeness": None,
            "contradictions": None,
            "additions": None,
        }

        # Extract data from each agent result
        for agent_result in agent_results:
            if not agent_result.success or not agent_result.data:
                continue

            agent_name = agent_result.agent_name
            data = agent_result.data

            if agent_name == "evaluate_completeness":
                aggregated["completeness"] = data
            elif agent_name == "evaluate_contradictions":
                aggregated["contradictions"] = data
            elif agent_name == "suggest_additions":
                aggregated["additions"] = data

        return aggregated


# Register graph for the evaluate_all operation
register_graph("pillars.evaluate_all", PillarsEvaluationGraph)
