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
    temperature = 0

    # Subclasses must define these
    prompt_template: str = ""
    default_suggestions: List[str] = []
    document_instructions = """**EVALUATION WITH DESIGN DOCUMENT CONTEXT**

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
    not_provided_prompt_template = (
        "You are evaluating the {aspect_name} aspect of a game concept.\n\n"
        "The router did not find any content related to {aspect_name} in the "
        "game concept.\n\n"
        "Your response should be:\n"
        '- status: "not_provided"\n'
        "- reasoning: Explain that this aspect was not addressed in the game\n"
        "  concept\n"
        "- suggestions: Provide 2-3 suggestions for what the creator should define\n"
        "  for this aspect\n\n"
        "Return a JSON response with these fields."
    )

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

        aspect_text = "\n\n".join(extracted_sections)
        pillar_section = self._build_pillar_section(data)
        document_section = self._build_document_section(data)
        context_section = self._build_context_section(
            aspect_text, pillar_section, document_section
        )

        # Format the base prompt
        formatted_prompt = self.prompt_template.format(
            aspect_name=self.aspect_name,
            context_section=context_section,
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
        assessment_marker = "## ASSESSMENT"
        if assessment_marker not in prompt:
            return self._inject_before_section(
                prompt, "## RESPONSE", self.document_instructions
            )

        search_start = prompt.find(assessment_marker) + len(assessment_marker)
        next_section_idx = self._find_next_section_index(
            prompt,
            search_start,
            ["## RESPONSE", "## EVALUATION CRITERIA", "## INSTRUCTIONS"],
        )
        return (
            prompt[:next_section_idx].rstrip()
            + "\n\n"
            + self.document_instructions
            + "\n\n"
            + prompt[next_section_idx:]
        )

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
        pillars_text = self._get_pillars_text(data)
        if not pillars_text:
            return ""

        return self._format_section(
            "DESIGN PILLARS",
            [
                "The game has the following established design pillars:",
                "",
                pillars_text,
                "",
                (
                    "**IMPORTANT**: Ensure your evaluation aligns with these design "
                    "pillars."
                ),
                "Do not suggest changes that would contradict the established pillars.",
                "Consider how this aspect supports or relates to the pillars.",
            ],
        )

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

        parts = [
            "The following information was extracted from an uploaded design document "
            "that may contain additional or different details about this aspect.",
            "",
        ]

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

        return self._format_section("DESIGN DOCUMENT CONTEXT", parts)

    def _build_not_provided_prompt(self) -> str:
        """Build prompt for when no content was extracted."""
        return self.not_provided_prompt_template.format(
            aspect_name=self.aspect_name.replace("_", " ")
        )

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
        """Get default suggestions for when aspect is not provided."""
        if self.default_suggestions:
            return self.default_suggestions
        return [
            f"Define the {self.aspect_name.replace('_', ' ')} for your game concept.",
        ]

    def _build_context_section(
        self, aspect_text: str, pillar_section: str, document_section: str
    ) -> str:
        parts = [aspect_text]
        if pillar_section:
            parts.append(pillar_section.strip())
        if document_section:
            parts.append(document_section.strip())
        return "\n\n".join(part for part in parts if part)

    def _get_pillars_text(self, data: Dict[str, Any]) -> str:
        pillar_context = data.get("pillar_context")
        if not pillar_context or not pillar_context.get("pillars_available", False):
            return ""

        pillars_text = pillar_context.get("pillars_text", "")
        if not pillars_text:
            pillars_text = pillar_context.get("all_pillars_text", "")
        return pillars_text or ""

    def _format_section(self, title: str, lines: List[str]) -> str:
        return "\n".join([f"## {title}", ""] + lines).strip()

    def _find_next_section_index(
        self, prompt: str, start: int, markers: List[str]
    ) -> int:
        next_idx = len(prompt)
        for marker in markers:
            idx = prompt.find(marker, start)
            if idx != -1 and idx < next_idx:
                next_idx = idx
        return next_idx

    def _inject_before_section(self, prompt: str, marker: str, text: str) -> str:
        if marker not in prompt:
            return prompt
        return prompt.replace(marker, text + "\n\n" + marker, 1)
