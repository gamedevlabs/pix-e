"""
Base class for V2 aspect agents.

All 10 aspect agents inherit from this class.
"""

from typing import Any, Dict, List

from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.schemas.v2.aspects import SimplifiedAspectResponse


class AspectAgentV2(V2BaseAgent):
    """
    Base class for simplified aspect evaluation agents.

    Subclasses must define:
    - name: Agent identifier (e.g., "player_experience_v2")
    - aspect_name: Aspect for DB storage (e.g., "player_experience")
    - prompt_template: The prompt template string
    """

    response_schema = SimplifiedAspectResponse
    temperature = 0.3  # Analytical evaluation

    # Subclasses must define these
    prompt_template: str = ""

    def validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data.

        For V2 agents, we expect extracted_sections from the router.
        """
        # extracted_sections can be empty (means not_provided)
        # No strict validation needed
        pass

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the evaluation prompt.

        Args:
            data: Contains 'extracted_sections' from router and optional
                  'pillar_context'

        Returns:
            Formatted prompt string
        """
        extracted_sections: List[str] = data.get("extracted_sections", [])

        if not extracted_sections:
            # Return prompt for not_provided case
            return self._build_not_provided_prompt()

        # Join sections for context
        aspect_text = "\n\n".join(extracted_sections)

        # Build pillar section if available
        pillar_section = self._build_pillar_section(data)

        return self.prompt_template.format(
            aspect_name=self.aspect_name,
            aspect_text=aspect_text,
            pillar_section=pillar_section,
        )

    def _build_pillar_section(self, data: Dict[str, Any]) -> str:
        """
        Build the pillar context section for the prompt.

        Args:
            data: May contain 'pillar_context' with pillar information.
                  In filtered mode, pillar_context already contains only
                  relevant pillars. In all mode, pillar_context contains
                  all pillars.

        Returns:
            Formatted pillar section or empty string if no pillars
        """
        pillar_context = data.get("pillar_context")
        if not pillar_context:
            return ""

        # Check if pillars are available
        if not pillar_context.get("pillars_available", False):
            return ""

        # Get pillars_text (already filtered for this aspect if in filtered mode)
        pillars_text = pillar_context.get("pillars_text", "")

        # Fallback to all_pillars_text for backward compatibility
        if not pillars_text:
            pillars_text = pillar_context.get("all_pillars_text", "")

        if not pillars_text:
            return ""

        return f"""
## DESIGN PILLARS

The game has the following established design pillars:

{pillars_text}

**IMPORTANT**: Ensure your evaluation aligns with these design pillars.
Do not suggest changes that would contradict the established pillars.
Consider how this aspect supports or relates to the pillars.
"""

    def _build_not_provided_prompt(self) -> str:
        """Build prompt for when no content was extracted."""
        return f"""You are evaluating the {self.aspect_name} aspect of a game concept.

The router did not find any content related to {self.aspect_name} in the game concept.

Your response should be:
- status: "not_provided"
- reasoning: Explain that this aspect was not addressed in the game
  concept
- suggestions: Provide 2-3 suggestions for what the creator should define
  for this aspect

Return a JSON response with these fields."""

    def should_skip_llm(self, data: Dict[str, Any]) -> bool:
        """
        Check if we should skip the LLM call.

        Returns True if no content was extracted for this aspect.
        In this case, we return a not_provided response without calling LLM.
        """
        extracted_sections = data.get("extracted_sections", [])
        return len(extracted_sections) == 0

    def get_not_provided_response(self) -> SimplifiedAspectResponse:
        """
        Get a not_provided response without calling LLM.

        Used when router found no content for this aspect.
        """
        return SimplifiedAspectResponse(
            aspect_name=self.aspect_name,
            status="not_provided",
            reasoning=(
                f"The game concept does not contain any information about "
                f"{self.aspect_name.replace('_', ' ')}. This aspect needs "
                f"to be defined."
            ),
            suggestions=self._get_default_suggestions(),
        )

    def _get_default_suggestions(self) -> List[str]:
        """
        Get default suggestions for when aspect is not provided.

        Subclasses should override this to provide aspect-specific suggestions.
        """
        return [
            f"Define the {self.aspect_name.replace('_', ' ')} for your game concept.",
        ]
