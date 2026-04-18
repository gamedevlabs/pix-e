"""
RQ1 normalization prompt.

Normalizes SPARC evaluation outputs into the RQ1 synthesis schema.
"""

RQ1_NORMALIZE_PROMPT = """You are normalizing SPARC evaluation output into a
standard RQ1 synthesis schema.

The input is an evaluation output JSON from a SPARC pipeline, not raw game text.
Do NOT re-evaluate the game concept. Only summarize what the evaluation states.
If information is missing, err on the side of "needs_work".

Input may include:
- Monolithic output: overall_assessment, aspects_evaluated, missing_aspects,
  suggestions, additional_details, readiness_verdict.
- Agentic output: aspect_results with per-aspect status/reasoning/suggestions,
  and/or synthesis with overall_status, strongest_aspects, weakest_aspects.

If a synthesis section is present, you may use it directly but still enforce
the constraints below.

Constraints:
- Core aspects: player_experience, gameplay, goals_challenges_rewards.
- Use ONLY these aspect names (snake_case):
  - player_experience
  - theme
  - purpose
  - gameplay
  - goals_challenges_rewards
  - place
  - story_narrative
  - unique_features
  - art_direction
  - opportunities_risks
- overall_status:
  - ready: all key aspects well-defined, no critical gaps
  - nearly_ready: most aspects defined, 1-2 need work
  - needs_work: significant gaps or any core aspect missing
- weakest_aspects must include ONLY aspects that need work or are not provided.
- critical_gaps must be a subset of weakest_aspects and only include blockers.
- If overall_status is "ready", weakest_aspects and critical_gaps must be empty.
- strongest_aspects/weakest_aspects: up to 3 items each.
- next_steps: 3-5 prioritized actions.
- Use null for consistency_notes if none.

EVALUATION TYPE:
%s

EVALUATION OUTPUT (JSON):
%s

RETURN JSON ONLY with this schema:
{
  "overall_status": "ready" | "nearly_ready" | "needs_work",
  "overall_reasoning": "2-3 sentence summary",
  "strongest_aspects": ["aspect_name", ... up to 3],
  "weakest_aspects": ["aspect_name", ... only needs_work or not_provided],
  "critical_gaps": ["aspect_name", ... blockers for prototyping],
  "next_steps": ["action", ... 3-5 items],
  "consistency_notes": "optional cross-aspect inconsistencies or synergies"
}
"""
