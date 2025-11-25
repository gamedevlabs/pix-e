"""
Pillar Context Agent for SPARC V2.

Fetches user's pillars and prepares context for aspect agents.
"""

from typing import Any, Dict

from llm.types import CapabilityRequirements
from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.prompts.v2.pillar_context import PILLAR_ASSIGNMENT_PROMPT
from sparc.llm.schemas.v2.pillar_context import PillarAssignmentsResponse


class PillarContextAgent(V2BaseAgent):
    """
    Agent that prepares pillar context for aspect evaluation.

    Supports two modes:
    - "all": All pillars provided to all aspects
    - "smart": Intelligently assigns pillars to relevant aspects
    """

    name = "pillar_context"
    aspect_name = "pillar_context"  # For DB storage
    response_schema = PillarAssignmentsResponse  # LLM returns just assignments

    capability_requirements = CapabilityRequirements(
        min_context_window=8000, json_strict=True
    )

    temperature = 0.2  # Low temperature for consistent assignments

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate required input fields."""
        if "pillars_text" not in data:
            raise ValueError("pillars_text is required")
        if "mode" not in data:
            raise ValueError("mode is required")
        if data["mode"] not in ["all", "smart"]:
            raise ValueError("mode must be 'all' or 'smart'")

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for pillar assignment (smart mode only)."""
        pillars_text = data["pillars_text"]
        mode = data["mode"]

        if mode == "all":
            # In "all" mode, we don't need LLM call
            # Just return a dummy prompt (won't be used)
            return ""

        # Smart mode: use LLM to assign pillars to aspects
        return PILLAR_ASSIGNMENT_PROMPT.format(pillars_text=pillars_text)
