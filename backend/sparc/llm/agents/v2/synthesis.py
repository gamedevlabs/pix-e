"""
Synthesis agent for SPARC V2.

Aggregates aspect evaluations into a final report.
"""

from typing import Any, Dict, List

from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.prompts.v2.synthesis import SYNTHESIS_PROMPT
from sparc.llm.schemas.v2.aspects import SimplifiedAspectResponse
from sparc.llm.schemas.v2.synthesis import SPARCSynthesis


class SynthesisAgent(V2BaseAgent):
    """
    Synthesis agent that aggregates all aspect evaluations.

    Takes the results from all 10 aspect agents and produces
    a final synthesis with cross-aspect analysis.
    """

    name = "synthesis"
    response_schema = SPARCSynthesis
    aspect_name = "synthesis"
    temperature = 0.3  # Analytical

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate that aspect_results are provided."""
        if not data.get("aspect_results"):
            raise ValueError("aspect_results is required")

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the synthesis prompt.

        Args:
            data: Contains 'aspect_results' dict of SimplifiedAspectResponse

        Returns:
            Formatted prompt string
        """
        aspect_results: Dict[str, SimplifiedAspectResponse] = data["aspect_results"]

        # Format aspect evaluations for the prompt
        evaluations = self._format_evaluations(aspect_results)

        return SYNTHESIS_PROMPT.format(aspect_evaluations=evaluations)

    def _format_evaluations(
        self, aspect_results: Dict[str, SimplifiedAspectResponse]
    ) -> str:
        """Format aspect results for the prompt."""
        lines = []

        for aspect_name, result in aspect_results.items():
            # Handle both dict and Pydantic model
            if isinstance(result, dict):
                status = result.get("status", "unknown")
                reasoning = result.get("reasoning", "")
                suggestions = result.get("suggestions", [])
            else:
                status = result.status
                reasoning = result.reasoning
                suggestions = result.suggestions

            lines.append(f"### {aspect_name.upper().replace('_', ' ')}")
            lines.append(f"Status: {status}")
            lines.append(f"Reasoning: {reasoning}")
            if suggestions:
                lines.append("Suggestions:")
                for s in suggestions[:3]:  # Limit to 3 suggestions
                    lines.append(f"  - {s}")
            lines.append("")

        return "\n".join(lines)

    def synthesize_without_llm(
        self, aspect_results: Dict[str, SimplifiedAspectResponse]
    ) -> SPARCSynthesis:
        """
        Create a basic synthesis without calling LLM.

        Useful for fallback or when synthesis agent fails.
        """
        well_defined = []
        needs_work = []
        not_provided = []

        for name, result in aspect_results.items():
            if isinstance(result, dict):
                status = result.get("status", "unknown")
            else:
                status = result.status

            if status == "well_defined":
                well_defined.append(name)
            elif status == "needs_work":
                needs_work.append(name)
            else:
                not_provided.append(name)

        # Determine overall status
        core_aspects = ["player_experience", "gameplay", "goals_challenges_rewards"]
        core_gaps = [a for a in core_aspects if a in not_provided or a in needs_work]

        if len(needs_work) == 0 and len(not_provided) == 0:
            overall_status = "ready"
        elif len(needs_work) <= 2 and len(not_provided) == 0:
            overall_status = "nearly_ready"
        else:
            overall_status = "needs_work"

        return SPARCSynthesis(
            overall_status=overall_status,
            overall_reasoning=self._generate_reasoning(
                well_defined, needs_work, not_provided
            ),
            strongest_aspects=well_defined[:3],
            weakest_aspects=(needs_work + not_provided)[:3],
            critical_gaps=core_gaps,
            next_steps=self._generate_next_steps(needs_work, not_provided),
            consistency_notes=None,
        )

    def _generate_reasoning(
        self, well_defined: List[str], needs_work: List[str], not_provided: List[str]
    ) -> str:
        """Generate basic reasoning text."""
        total = len(well_defined) + len(needs_work) + len(not_provided)
        return (
            f"The game concept has {len(well_defined)} well-defined aspects, "
            f"{len(needs_work)} aspects needing work, and "
            f"{len(not_provided)} aspects not addressed out of {total} total."
        )

    def _generate_next_steps(
        self, needs_work: List[str], not_provided: List[str]
    ) -> List[str]:
        """Generate basic next steps."""
        steps = []
        for aspect in not_provided[:2]:
            steps.append(f"Define the {aspect.replace('_', ' ')} aspect.")
        for aspect in needs_work[:3]:
            steps.append(f"Improve the {aspect.replace('_', ' ')} definition.")
        return steps[:5]
