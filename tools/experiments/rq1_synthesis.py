from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from llm.providers.manager import ModelManager


class RQ1Synthesis(BaseModel):
    overall_status: str = Field(
        description="ready | nearly_ready | needs_work"
    )
    overall_reasoning: str = Field(
        description="2-3 sentence summary of the concept evaluation"
    )
    strongest_aspects: List[str] = Field(
        default_factory=list, description="Top 3 strongest aspects"
    )
    weakest_aspects: List[str] = Field(
        default_factory=list, description="Top 3 weakest aspects"
    )
    critical_gaps: List[str] = Field(
        default_factory=list, description="Key gaps blocking prototyping"
    )
    next_steps: List[str] = Field(
        default_factory=list, description="Prioritized actions to improve concept"
    )
    consistency_notes: str = Field(
        default="", description="Cross-aspect inconsistencies or synergies"
    )


SYNTHESIS_PROMPT = """You are synthesizing a SPARC evaluation into a final summary.
Return JSON only that matches the schema.

Inputs may come from a monolithic evaluation or from aspect agents.
Focus on grounded, concise conclusions, not verbosity.

Evaluation Input:
{input_text}
"""

ASPECT_ORDER = [
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



def _format_monolithic(results: Dict[str, Any]) -> str:
    overview = results.get("overall_assessment", "")
    readiness = results.get("readiness_verdict", "")
    missing = results.get("missing_aspects") or []
    suggestions = (results.get("suggestions") or []) + (
        results.get("additional_details") or []
    )

    aspect_notes: Dict[str, str] = {}
    for aspect in results.get("aspects_evaluated") or []:
        name = aspect.get("aspect_name", "")
        assessment = aspect.get("assessment", "")
        if name:
            aspect_notes[name] = assessment

    return _format_unified_input(
        overview=overview,
        readiness=readiness,
        missing_aspects=missing,
        suggestions=suggestions,
        aspect_notes=aspect_notes,
    )


def _format_aspects(aspect_results: Dict[str, Any]) -> str:
    missing = [
        name
        for name, result in aspect_results.items()
        if result.get("status") == "not_provided"
    ]
    suggestions: List[str] = []
    aspect_notes: Dict[str, Dict[str, Any]] = {}
    for aspect_name, result in aspect_results.items():
        aspect_notes[aspect_name] = result
        for suggestion in result.get("suggestions", [])[:1]:
            suggestions.append(suggestion)
    return _format_unified_input(
        overview="N/A (use aspect results below)",
        readiness="N/A",
        missing_aspects=missing,
        suggestions=suggestions,
        aspect_notes=aspect_notes,
    )


def _format_unified_input(
    *,
    overview: str,
    readiness: str,
    missing_aspects: List[str],
    suggestions: List[str],
    aspect_notes: Dict[str, Any],
) -> str:
    parts: List[str] = []
    parts.append("Overview:")
    parts.append(f"- Overall: {overview}")
    parts.append(f"- Readiness: {readiness}")

    parts.append("Missing Aspects:")
    if missing_aspects:
        parts.append(f"- {', '.join(missing_aspects)}")
    else:
        parts.append("- None")

    parts.append("Suggestions:")
    if suggestions:
        for suggestion in suggestions[:6]:
            parts.append(f"- {suggestion}")
    else:
        parts.append("- None")

    parts.append("Aspect Results:")
    for aspect_name in ASPECT_ORDER:
        raw = aspect_notes.get(aspect_name, {})
        if isinstance(raw, dict):
            status = raw.get("status", "")
            reasoning = raw.get("reasoning", "")
            if not status and "assessment" in raw:
                status = "needs_work" if aspect_name in missing_aspects else "well_defined"
                reasoning = raw.get("assessment", "")
            parts.append(f"- {aspect_name} [{status}]: {reasoning}")
            suggestions_list = raw.get("suggestions", [])
            if suggestions_list:
                for suggestion in suggestions_list[:2]:
                    parts.append(f"  - {suggestion}")
        elif raw:
            parts.append(f"- {aspect_name}: {raw}")
    return "\n".join(parts)


def build_synthesis_input(mode: str, results: Dict[str, Any]) -> str:
    if mode == "monolithic":
        return _format_monolithic(results)
    aspect_results = results.get("aspect_results") or {}
    return _format_aspects(aspect_results)


def run_rq1_synthesis(
    *,
    model_name: str,
    mode: str,
    results: Dict[str, Any],
) -> Dict[str, Any]:
    input_text = build_synthesis_input(mode, results)
    prompt = SYNTHESIS_PROMPT.format(input_text=input_text)
    manager = ModelManager()
    structured = manager.generate_structured_with_model(
        model_name=model_name,
        prompt=prompt,
        response_schema=RQ1Synthesis,
        temperature=0,
    )
    data = structured.data if hasattr(structured, "data") else structured
    return data.model_dump() if hasattr(data, "model_dump") else data
