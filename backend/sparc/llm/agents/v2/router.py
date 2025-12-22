"""
Router agent for SPARC V2.

Extracts relevant portions of game concepts for each aspect.
"""

import time
from typing import Any, Dict, List

from llm.types import AgentResult, ErrorInfo
from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.prompts.v2.router import ROUTER_PROMPT
from sparc.llm.schemas.v2.router import RouterResponse

# All 10 SPARC aspects
ALL_ASPECTS = [
    "player_experience",
    "theme",
    "purpose",
    "gameplay",
    "goals_challenges_rewards",
    "place",
    "story_narrative",
    "unique_features",
    "art_direction",
    "opportunities_risks",
]


class RouterAgent(V2BaseAgent):
    """
    Router agent that extracts aspect-relevant content from game concepts.

    Takes the full game concept and extracts relevant sections for each
    target aspect. Downstream agents receive only their relevant content.
    """

    name = "router"
    response_schema = RouterResponse
    aspect_name = "router"
    temperature = 0

    def __init__(self, max_retries: int = 3):
        """
        Initialize router agent.

        Args:
            max_retries: Maximum retry attempts on failure
        """
        super().__init__()
        self.max_retries = max_retries

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate that game_text is provided."""
        if not data.get("game_text"):
            raise ValueError("game_text is required")

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build the router prompt."""
        game_text = data["game_text"]
        target_aspects = data.get("target_aspects", ALL_ASPECTS)

        # Format target aspects for the prompt
        if target_aspects == "all" or target_aspects == ALL_ASPECTS:
            aspects_str = "ALL ASPECTS (extract for all 10 aspects)"
        else:
            aspects_str = ", ".join(target_aspects)

        return ROUTER_PROMPT.format(
            game_text=game_text,
            target_aspects=aspects_str,
        )

    def execute_with_retry(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute with retry logic.

        Args:
            context: Execution context

        Returns:
            AgentResult from successful execution or final failure
        """
        last_error = None

        for attempt in range(self.max_retries):
            result = self.execute(context)

            if result.success:
                return result

            last_error = result.error
            if attempt < self.max_retries - 1:
                continue

        return AgentResult(
            agent_name=self.name,
            success=False,
            data=None,
            model_used=None,
            execution_time_ms=0,
            error=ErrorInfo(
                code="ROUTER_FAILED",
                message=f"Router failed after {self.max_retries} attempts",
                severity="error",
                context={
                    "last_error": last_error.message if last_error else "Unknown",
                },
            ),
        )

    async def run_with_retry(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute asynchronously with retry logic.

        Args:
            context: Execution context

        Returns:
            AgentResult from successful execution or final failure
        """
        start_time = time.time()
        last_error = None
        total_tokens = 0

        for attempt in range(self.max_retries):
            result = await self.run(context)

            if result.success:
                return result

            last_error = result.error
            total_tokens += result.total_tokens
            if attempt < self.max_retries - 1:
                continue

        execution_time_ms = int((time.time() - start_time) * 1000)
        return AgentResult(
            agent_name=self.name,
            success=False,
            data=None,
            model_used=None,
            execution_time_ms=execution_time_ms,
            total_tokens=total_tokens,
            error=ErrorInfo(
                code="ROUTER_FAILED",
                message=f"Router failed after {self.max_retries} attempts",
                severity="error",
                context={
                    "last_error": last_error.message if last_error else "Unknown",
                },
            ),
        )

    def get_aspects_with_content(self, router_response: RouterResponse) -> List[str]:
        """
        Get list of aspects that have extracted content.

        Args:
            router_response: The router's response

        Returns:
            List of aspect names that have content
        """
        return [
            ext.aspect_name
            for ext in router_response.extractions
            if len(ext.extracted_sections) > 0
        ]
