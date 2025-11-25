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
                  'pillar_context', 'document_sections', 'document_insights'

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

        document_section = self._build_document_section(data)
        if document_section:
            pillar_section = pillar_section + "\n" + document_section

        # Format the base prompt
        formatted_prompt = self.prompt_template.format(
            aspect_name=self.aspect_name,
            aspect_text=aspect_text,
            pillar_section=pillar_section,
        )

        # Inject shared evaluation instructions if document context is present
        # This ensures all aspect agents consider document context when available
        has_document_context = bool(
            data.get("document_sections") or data.get("document_insights")
        )
        if has_document_context:
            formatted_prompt = self._inject_document_context_instructions(
                formatted_prompt
            )

        return formatted_prompt

    def _inject_document_context_instructions(self, prompt: str) -> str:
        """
        Inject shared instructions about using document context into the prompt.

        This method finds the ASSESSMENT section and adds instructions about
        considering document context, avoiding duplication across all prompts.

        Args:
            prompt: The formatted prompt string

        Returns:
            Prompt with document context instructions injected
        """
        # Check if ASSESSMENT section exists
        if "## ASSESSMENT" not in prompt:
            # If no ASSESSMENT section, add instructions before RESPONSE
            if "## RESPONSE" in prompt:
                instructions = self._get_document_context_instructions()
                return prompt.replace("## RESPONSE", instructions + "\n\n## RESPONSE")
            return prompt

        # Find the ASSESSMENT section and inject instructions at the end of it
        assessment_marker = "## ASSESSMENT"
        assessment_idx = prompt.find(assessment_marker)

        if assessment_idx == -1:
            return prompt

        # Find the end of ASSESSMENT section (next ## section or end of string)
        # Start searching after the ASSESSMENT marker
        search_start = assessment_idx + len(assessment_marker)
        next_section_idx = len(prompt)

        # Look for the next section marker
        for marker in ["## RESPONSE", "## EVALUATION CRITERIA", "## INSTRUCTIONS"]:
            idx = prompt.find(marker, search_start)
            if idx != -1 and idx < next_section_idx:
                next_section_idx = idx

        # Insert instructions right before the next section
        instructions = self._get_document_context_instructions()
        return (
            prompt[:next_section_idx].rstrip()
            + "\n\n"
            + instructions
            + "\n\n"
            + prompt[next_section_idx:]
        )

    def _get_document_context_instructions(self) -> str:
        """
        Get shared instructions for evaluating with document context.

        Returns:
            Instructions string to inject into prompts
        """
        return """**EVALUATION WITH DESIGN DOCUMENT CONTEXT**

When evaluating this aspect, consider:
- The game concept content provided above
- Any design document context (if provided in the DESIGN DOCUMENT CONTEXT section)
- Design pillars (if provided in the DESIGN PILLARS section)

**IMPORTANT**: If design document context is provided, consider how it
relates to or differs from the game concept. Your evaluation should reflect
information from BOTH sources when available. If the document provides
additional details, constraints, or different information not mentioned in
the game concept, incorporate them into your evaluation and mention this
in your reasoning."""

    def _build_pillar_section(self, data: Dict[str, Any]) -> str:
        """
        Build the pillar context section for the prompt.

        Args:
            data: May contain 'pillar_context' with pillar information.
                  In smart mode, pillar_context already contains only
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

        # Get pillars_text (already smartly assigned for this aspect if in smart mode)
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

    def _build_document_section(self, data: Dict[str, Any]) -> str:
        """
        Build the document context section for the prompt.

        Args:
            data: May contain 'document_sections' and 'document_insights'
                  extracted from uploaded design document.

        Returns:
            Formatted document section or empty string if no document context
        """
        document_sections = data.get("document_sections", [])
        document_insights = data.get("document_insights", [])

        if not document_sections and not document_insights:
            return ""

        parts = ["## DESIGN DOCUMENT CONTEXT", ""]
        parts.append(
            "The following information was extracted from an uploaded design document "
            "that may contain additional or different details about this aspect."
        )
        parts.append("")

        if document_sections:
            parts.append("**Relevant sections from the design document:**")
            parts.append("")
            for i, section in enumerate(document_sections, 1):
                parts.append(f"{i}. {section}")
            parts.append("")

        if document_insights:
            parts.append("**Key design decisions and constraints from the document:**")
            parts.append("")
            for i, insight in enumerate(document_insights, 1):
                parts.append(f"{i}. {insight}")
            parts.append("")

        parts.append(
            "**IMPORTANT**: When evaluating this aspect, consider BOTH the "
            "game concept content above AND this design document context. "
            "If the document provides additional locations, details, or "
            "constraints not mentioned in the game concept, incorporate them "
            "into your evaluation. Note any differences or conflicts between "
            "the two sources in your reasoning."
        )

        return "\n".join(parts)

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
