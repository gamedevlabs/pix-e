"""
V2 Base Agent with DB tracking.

Extends BaseAgent to automatically persist each LLM call to the database.
"""

from typing import Any, Dict, Optional

from llm.agent_runtime import BaseAgent
from llm.types import AgentResult
from sparc.models import SPARCEvaluation, SPARCEvaluationResult

# Model costs per 1M tokens in EUR
MODEL_COSTS = {
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free
    "gpt-4o-mini": {"input": 0.135, "output": 0.540},  # $0.150/$0.600
    "gpt-4o": {"input": 2.25, "output": 9.00},  # $2.50/$10.00
}


def calculate_cost_eur(
    model_name: str, prompt_tokens: int = 0, completion_tokens: int = 0
) -> float:
    """
    Calculate cost in EUR based on actual token usage and model pricing.
    """
    costs = MODEL_COSTS.get(model_name, {"input": 0.0, "output": 0.0})
    input_cost = (prompt_tokens / 1_000_000) * costs["input"]
    output_cost = (completion_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 8)


class V2BaseAgent(BaseAgent):
    """
    Extended base agent with per-call DB persistence.

    Automatically saves each LLM call to SPARCEvaluationResult
    with full tracking of tokens, timing, costs, and input/output.
    """

    # Subclasses should set this to the aspect name for DB storage
    aspect_name: str = ""

    def execute_and_save(
        self,
        context: Dict[str, Any],
        evaluation: Optional[SPARCEvaluation] = None,
    ) -> AgentResult:
        """
        Execute the agent and save result to database.

        Args:
            context: Execution context with model_manager and data
            evaluation: Parent SPARCEvaluation to link results to

        Returns:
            AgentResult with execution details
        """
        # Get input data before execution
        input_data = context.get("data", {})

        # Execute the agent
        result = self.execute(context)

        # Save to database if evaluation is provided
        if evaluation is not None:
            self._save_result(
                evaluation=evaluation,
                input_data=input_data,
                result=result,
            )

        return result

    async def run_and_save(
        self,
        context: Dict[str, Any],
        evaluation: Optional[SPARCEvaluation] = None,
    ) -> AgentResult:
        """
        Execute the agent asynchronously and save result to database.

        Args:
            context: Execution context with model_manager and data
            evaluation: Parent SPARCEvaluation to link results to

        Returns:
            AgentResult with execution details
        """
        # Get input data before execution
        input_data = context.get("data", {})

        # Execute the agent
        result = await self.run(context)

        # Save to database if evaluation is provided
        if evaluation is not None:
            self._save_result(
                evaluation=evaluation,
                input_data=input_data,
                result=result,
            )

        return result

    def _save_result(
        self,
        evaluation: SPARCEvaluation,
        input_data: Dict[str, Any],
        result: AgentResult,
    ) -> SPARCEvaluationResult:
        """
        Persist LLM call result to database.

        Args:
            evaluation: Parent evaluation session
            input_data: What was sent to the agent
            result: AgentResult from execution

        Returns:
            Created SPARCEvaluationResult instance
        """
        # Calculate cost
        model_name = result.model_used or ""
        cost_eur = calculate_cost_eur(
            model_name=model_name,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
        )

        # Prepare result data
        result_data = result.data if result.success else None
        if result.error:
            result_data = {
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                }
            }

        # Create and save the result record
        db_result = SPARCEvaluationResult.objects.create(
            evaluation=evaluation,
            aspect=self.aspect_name or self.name,
            agent_name=self.name,
            model_used=model_name,
            execution_time_ms=result.execution_time_ms,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            estimated_cost_eur=cost_eur,
            input_data=input_data,
            result_data=result_data or {},
        )

        return db_result
