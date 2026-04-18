"""
RQ1 LLM-as-a-Judge — Blinded comparative scoring of three evaluation arms.

For each concept, presents the original game text alongside all 3 evaluations
(anonymized as A/B/C with randomized assignment) to a stronger judge model.
The judge scores each evaluation on 5 rubric dimensions — with per-dimension
evidence requirements — and ranks them.

Position bias is mitigated by running multiple rotations per concept
(different arm orderings) and averaging scores.

Usage:
    python tools/experiments/run_rq1_judge.py \
        --run-dir docs/experiments/rq1_v2_run_20260303_222619

    python tools/experiments/run_rq1_judge.py \
        --run-dir docs/experiments/rq1_v2_run_20260303_222619 \
        --judge-model gpt-4o --max-parallel 3 --rotations 3

    python tools/experiments/run_rq1_judge.py \
        --run-dir docs/experiments/rq1_v2_run_20260303_222619 --dry-run
"""

import argparse
import json
import os
import random
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Literal

import django

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DimensionAnalysis(BaseModel):
    evidence: str = Field(
        description="1-2 sentences citing specific examples from the evaluation",
    )
    score: int = Field(ge=1, le=5)


class DetailedEvaluationScore(BaseModel):
    accuracy: DimensionAnalysis
    specificity: DimensionAnalysis
    actionability: DimensionAnalysis
    internal_consistency: DimensionAnalysis
    calibration: DimensionAnalysis


class JudgeResponse(BaseModel):
    evaluation_a: DetailedEvaluationScore
    evaluation_b: DetailedEvaluationScore
    evaluation_c: DetailedEvaluationScore
    ranking: List[Literal["A", "B", "C"]]
    justification: str


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

JUDGE_PROMPT = """You are an expert game design evaluator acting as a judge.

You will be given:
1. A GAME CONCEPT — the original game idea text written by a designer
2. Three EVALUATIONS (A, B, C) of that game concept, each produced by a \
different evaluation pipeline

Your task: score each evaluation on 5 dimensions (1-5 scale) and rank them.

## GAME CONCEPT

{game_text}

## EVALUATION A

{evaluation_a}

## EVALUATION B

{evaluation_b}

## EVALUATION C

{evaluation_c}

## SCORING RUBRIC

Score each evaluation on these 5 dimensions (1 = poor, 5 = excellent).

IMPORTANT: Each dimension measures something DIFFERENT. You MUST evaluate \
each dimension independently. It is common and expected for dimensions to \
receive different scores. For example:
- An evaluation can have correct status labels (high accuracy) but use \
generic language (low specificity).
- An evaluation can quote the game text extensively (high specificity) but \
give vague suggestions (low actionability).
- An evaluation's synthesis can match its aspects (high internal consistency) \
but still have a miscalibrated overall_status (low calibration).

For EACH dimension, you MUST provide specific evidence from the evaluation \
text that justifies your score BEFORE assigning the score.

### 1. Accuracy (1-5)
Does the evaluation correctly identify what the game text covers vs. what is \
missing? Are the status labels (well_defined / needs_work / not_provided) \
appropriate given the actual content of the game text?
- 5: Every status label is justified; nothing is miscategorized
- 4: Nearly all labels correct; at most 1 debatable
- 3: Most labels are correct but 2-3 are debatable
- 2: Several labels are clearly wrong
- 1: Multiple statuses are clearly wrong

To score this: Compare each aspect's status with what the game text actually \
covers. Quote specific passages from the game text that support or contradict \
the assigned status.

### 2. Specificity (1-5)
Are assessments grounded in the actual game text — referencing or quoting \
specific details — or are they generic boilerplate that could apply to any game?
- 5: Reasoning consistently references specific elements from the game text \
(character names, mechanic names, specific verbs, narrative details)
- 4: Most reasoning references specifics, with occasional generic statements
- 3: Mix of specific references and generic statements
- 2: Mostly generic with rare specific references
- 1: Entirely generic; could be copy-pasted for any game concept

To score this: Count how many aspect reasonings reference specific elements \
from the game text vs. how many use generic phrases like "well-described" or \
"clearly articulated" without citing what exactly is described.

### 3. Actionability (1-5)
Are suggestions concrete, prioritized, and useful for a game designer?
- 5: Suggestions are specific, immediately actionable, and well-prioritized
- 4: Most suggestions are actionable and specific
- 3: Suggestions are reasonable but somewhat vague or unprioritized
- 2: Suggestions are mostly generic or obvious
- 1: Suggestions are too abstract or obvious to be useful

To score this: Look at the suggestions across aspects. Can a game designer \
act on them immediately, or are they generic advice like "add more detail"?

### 4. Internal Consistency (1-5)
Do the individual aspect statuses logically align with the synthesis \
(overall_status, strongest_aspects, weakest_aspects, critical_gaps)?
- 5: Synthesis perfectly reflects the aspect evaluations
- 4: Synthesis mostly reflects aspects; at most 1 minor inconsistency
- 3: Minor inconsistencies (e.g., an aspect listed as strongest but rated \
needs_work)
- 2: Notable inconsistencies between aspects and synthesis
- 1: Synthesis contradicts the aspect evaluations

To score this: Check that strongest_aspects lists only well_defined aspects, \
weakest_aspects lists only needs_work/not_provided aspects, and critical_gaps \
is a subset of weakest_aspects.

### 5. Calibration (1-5)
Is the overall_status appropriate? A concept with many needs_work aspects \
should not be rated "ready". A concept with mostly well_defined aspects \
should not be "needs_work".
- 5: Overall status perfectly matches the distribution of aspect statuses
- 4: Overall status is reasonable, very slight leniency or harshness
- 3: Slightly too lenient or too harsh
- 2: Noticeably miscalibrated
- 1: Clearly miscalibrated

To score this: Count the number of well_defined, needs_work, and not_provided \
statuses. Then check if the overall_status follows these rules: "ready" \
requires all key aspects well_defined; "nearly_ready" allows 1-2 needs_work; \
"needs_work" means 3+ needs_work or any not_provided in core aspects.

## RANKING

After scoring, rank the three evaluations from best (1st) to worst (3rd). \
Provide a brief 2-3 sentence justification for your ranking.

## RESPONSE FORMAT

Return a JSON object with scores for each evaluation and a ranking. \
Each dimension score must include an "evidence" field (1-2 sentences) and \
a "score" field (1-5). \
The ranking array should list letters from best to worst (e.g., ["B","A","C"] \
means B is best, A is second, C is worst).
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ARM_KEYS = ("monolithic", "agentic_full_text", "agentic_routed")


def _format_evaluation(response: Dict[str, Any]) -> str:
    """Format an RQ1UnifiedResponse dict as readable text for the judge."""
    lines: List[str] = []

    aspect_results = response.get("aspect_results", {})
    for aspect_name, aspect in aspect_results.items():
        label = aspect_name.replace("_", " ").title()
        status = aspect.get("status", "unknown")
        reasoning = aspect.get("reasoning", "")
        suggestions = aspect.get("suggestions", [])

        lines.append(f"### {label}")
        lines.append(f"Status: {status}")
        lines.append(f"Reasoning: {reasoning}")
        if suggestions:
            lines.append("Suggestions:")
            for s in suggestions:
                lines.append(f"  - {s}")
        lines.append("")

    synthesis = response.get("synthesis", {})
    if synthesis:
        lines.append("### Synthesis")
        lines.append(f"Overall Status: {synthesis.get('overall_status', '')}")
        lines.append(
            f"Overall Reasoning: {synthesis.get('overall_reasoning', '')}"
        )
        strongest = synthesis.get("strongest_aspects", [])
        lines.append(f"Strongest Aspects: {', '.join(strongest) if strongest else 'None'}")
        weakest = synthesis.get("weakest_aspects", [])
        lines.append(f"Weakest Aspects: {', '.join(weakest) if weakest else 'None'}")
        gaps = synthesis.get("critical_gaps", [])
        lines.append(f"Critical Gaps: {', '.join(gaps) if gaps else 'None'}")
        steps = synthesis.get("next_steps", [])
        if steps:
            lines.append("Next Steps:")
            for s in steps:
                lines.append(f"  - {s}")
        consistency = synthesis.get("consistency_notes")
        if consistency:
            lines.append(f"Consistency Notes: {consistency}")

    return "\n".join(lines)


def _build_anonymized_prompt(
    game_text: str,
    responses: Dict[str, Dict[str, Any]],
    seed: int,
) -> tuple[str, Dict[str, str]]:
    """
    Build a judge prompt with randomized A/B/C assignment.

    Returns (prompt, mapping) where mapping is e.g.
    {"A": "monolithic", "B": "agentic_routed", "C": "agentic_full_text"}.
    """
    rng = random.Random(seed)
    arms = list(ARM_KEYS)
    rng.shuffle(arms)

    labels = ["A", "B", "C"]
    mapping = {label: arm for label, arm in zip(labels, arms)}

    formatted = {}
    for label, arm in mapping.items():
        formatted[label] = _format_evaluation(responses[arm])

    prompt = JUDGE_PROMPT.format(
        game_text=game_text,
        evaluation_a=formatted["A"],
        evaluation_b=formatted["B"],
        evaluation_c=formatted["C"],
    )

    return prompt, mapping


def _extract_score(dim: DimensionAnalysis) -> int:
    """Extract the numeric score from a DimensionAnalysis."""
    return dim.score


def _score_total(score: DetailedEvaluationScore) -> int:
    return (
        _extract_score(score.accuracy)
        + _extract_score(score.specificity)
        + _extract_score(score.actionability)
        + _extract_score(score.internal_consistency)
        + _extract_score(score.calibration)
    )


def _score_to_dict(score: DetailedEvaluationScore, label: str) -> Dict[str, Any]:
    """Convert a DetailedEvaluationScore to a dict for output."""
    return {
        "label": label,
        "accuracy": _extract_score(score.accuracy),
        "accuracy_evidence": score.accuracy.evidence,
        "specificity": _extract_score(score.specificity),
        "specificity_evidence": score.specificity.evidence,
        "actionability": _extract_score(score.actionability),
        "actionability_evidence": score.actionability.evidence,
        "internal_consistency": _extract_score(score.internal_consistency),
        "internal_consistency_evidence": score.internal_consistency.evidence,
        "calibration": _extract_score(score.calibration),
        "calibration_evidence": score.calibration.evidence,
        "total": _score_total(score),
    }


# ---------------------------------------------------------------------------
# Judge a single concept (one rotation)
# ---------------------------------------------------------------------------

def _judge_concept_single(
    *,
    concept_row: Dict[str, Any],
    judge_model: str,
    rotation: int,
    index: int,
    total: int,
) -> Dict[str, Any]:
    """Judge one concept's three arm evaluations with a single rotation."""
    from llm.config import get_config
    from llm.cost_tracking import calculate_cost_eur
    from llm.logfire_config import get_logfire
    from llm.providers.manager import ModelManager

    logfire = get_logfire()
    config = get_config()
    manager = ModelManager(config)

    project_name = concept_row["project_name"]
    game_text = concept_row.get("game_text", "")

    if not game_text:
        return {
            "project_id": concept_row.get("project_id"),
            "project_name": project_name,
            "concept_id": concept_row.get("concept_id"),
            "success": False,
            "error": "No game_text available for judging",
        }

    # Collect responses
    responses = {}
    for arm in ARM_KEYS:
        arm_data = concept_row.get(arm, {})
        if not arm_data.get("success") or not arm_data.get("response"):
            return {
                "project_id": concept_row.get("project_id"),
                "project_name": project_name,
                "concept_id": concept_row.get("concept_id"),
                "success": False,
                "error": f"Arm '{arm}' has no successful response",
            }
        responses[arm] = arm_data["response"]

    # Build anonymized prompt with rotation-specific seed
    base_seed = hash(f"{concept_row.get('concept_id', index)}")
    seed = base_seed + rotation
    prompt, mapping = _build_anonymized_prompt(game_text, responses, seed)
    arm_to_label = {arm: label for label, arm in mapping.items()}

    with logfire.span(
        "Judge: {project_name} [{index}/{total}] rot={rotation}",
        project_name=project_name,
        index=index,
        total=total,
        rotation=rotation,
        mapping=mapping,
    ):
        start = time.time()
        result = manager.generate_structured_with_model(
            model_name=judge_model,
            prompt=prompt,
            response_schema=JudgeResponse,
            temperature=0,
        )
        elapsed_ms = int((time.time() - start) * 1000)

        prompt_tokens = result.prompt_tokens
        completion_tokens = result.completion_tokens
        total_tokens = result.total_tokens
        cost = float(
            calculate_cost_eur(judge_model, prompt_tokens, completion_tokens)
        )

        judge_data = result.data
        scores_by_label = {
            "A": judge_data.evaluation_a,
            "B": judge_data.evaluation_b,
            "C": judge_data.evaluation_c,
        }

        # De-anonymize: map scores back to arm names
        scores_by_arm = {}
        for arm in ARM_KEYS:
            label = arm_to_label[arm]
            scores_by_arm[arm] = _score_to_dict(scores_by_label[label], label)

        # De-anonymize ranking
        ranking_arms = [mapping[label] for label in judge_data.ranking]

        logfire.info(
            "Judged {project_name} rot={rotation}: winner={winner}, "
            "mono={mono_total}, full={full_total}, routed={routed_total}",
            project_name=project_name,
            rotation=rotation,
            winner=ranking_arms[0] if ranking_arms else "unknown",
            mono_total=scores_by_arm["monolithic"]["total"],
            full_total=scores_by_arm["agentic_full_text"]["total"],
            routed_total=scores_by_arm["agentic_routed"]["total"],
        )

    return {
        "project_id": concept_row.get("project_id"),
        "project_name": project_name,
        "concept_id": concept_row.get("concept_id"),
        "rotation": rotation,
        "success": True,
        "mapping": mapping,
        "scores": scores_by_arm,
        "ranking": ranking_arms,
        "justification": judge_data.justification,
        "judge_model": judge_model,
        "execution_time_ms": elapsed_ms,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_eur": cost,
    }


DIMENSIONS = [
    "accuracy", "specificity", "actionability",
    "internal_consistency", "calibration",
]


def _judge_concept(
    *,
    concept_row: Dict[str, Any],
    judge_model: str,
    rotations: int,
    index: int,
    total: int,
) -> Dict[str, Any]:
    """
    Judge one concept with multiple rotations and average scores.

    Each rotation uses a different arm ordering to cancel position bias.
    """
    rotation_results: List[Dict[str, Any]] = []

    for rotation in range(rotations):
        result = _judge_concept_single(
            concept_row=concept_row,
            judge_model=judge_model,
            rotation=rotation,
            index=index,
            total=total,
        )
        rotation_results.append(result)
        if not result.get("success"):
            return result  # Early exit on failure

    # Average scores across rotations
    avg_scores: Dict[str, Dict[str, Any]] = {}
    for arm in ARM_KEYS:
        arm_totals: Dict[str, float] = {d: 0.0 for d in DIMENSIONS}
        for r in rotation_results:
            for d in DIMENSIONS:
                arm_totals[d] += r["scores"][arm][d]
        avg: Dict[str, Any] = {
            d: round(arm_totals[d] / rotations, 2) for d in DIMENSIONS
        }
        avg["total"] = round(sum(avg[d] for d in DIMENSIONS), 2)
        # Collect evidence from all rotations
        evidence: Dict[str, List[str]] = {d: [] for d in DIMENSIONS}
        for r in rotation_results:
            for d in DIMENSIONS:
                ev = r["scores"][arm].get(f"{d}_evidence", "")
                if ev:
                    evidence[d].append(ev)
        for d in DIMENSIONS:
            avg[f"{d}_evidence"] = evidence[d]
        avg_scores[arm] = avg

    # Aggregate ranking: count 1st-place wins across rotations
    rank_wins: Dict[str, int] = {arm: 0 for arm in ARM_KEYS}
    for r in rotation_results:
        if r["ranking"]:
            rank_wins[r["ranking"][0]] += 1
    ranking = sorted(ARM_KEYS, key=lambda a: (-rank_wins[a], -avg_scores[a]["total"]))

    # Cost totals
    total_cost = sum(r.get("estimated_cost_eur", 0.0) for r in rotation_results)
    total_tokens_sum = sum(r.get("total_tokens", 0) for r in rotation_results)
    prompt_tokens_sum = sum(r.get("prompt_tokens", 0) for r in rotation_results)
    completion_tokens_sum = sum(r.get("completion_tokens", 0) for r in rotation_results)
    elapsed_ms_sum = sum(r.get("execution_time_ms", 0) for r in rotation_results)

    return {
        "project_id": concept_row.get("project_id"),
        "project_name": concept_row["project_name"],
        "concept_id": concept_row.get("concept_id"),
        "success": True,
        "rotations": rotations,
        "scores": avg_scores,
        "ranking": ranking,
        "rank_wins": rank_wins,
        "rotation_details": rotation_results,
        "judge_model": judge_model,
        "execution_time_ms": elapsed_ms_sum,
        "total_tokens": total_tokens_sum,
        "prompt_tokens": prompt_tokens_sum,
        "completion_tokens": completion_tokens_sum,
        "estimated_cost_eur": total_cost,
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def _build_summary(
    results: List[Dict[str, Any]],
    judge_model: str,
    started_at: str,
    rotations: int,
) -> Dict[str, Any]:
    """Build aggregated summary from individual judge results."""
    successful = [r for r in results if r.get("success")]
    n = len(successful)
    if n == 0:
        return {"error": "No successful judge results", "total_concepts": 0}

    all_dimensions = DIMENSIONS + ["total"]

    # Per-arm mean scores
    arm_scores: Dict[str, Dict[str, List[float]]] = {
        arm: {d: [] for d in all_dimensions} for arm in ARM_KEYS
    }
    # Win counts (1st place in averaged ranking)
    win_counts: Dict[str, int] = {arm: 0 for arm in ARM_KEYS}

    for r in successful:
        scores = r["scores"]
        ranking = r["ranking"]
        if ranking:
            win_counts[ranking[0]] += 1
        for arm in ARM_KEYS:
            for d in all_dimensions:
                arm_scores[arm][d].append(scores[arm][d])

    # Compute means
    arm_means: Dict[str, Dict[str, float]] = {}
    for arm in ARM_KEYS:
        arm_means[arm] = {}
        for d in all_dimensions:
            values = arm_scores[arm][d]
            arm_means[arm][d] = round(sum(values) / len(values), 2) if values else 0.0

    # Cost totals
    total_cost = sum(r.get("estimated_cost_eur", 0.0) for r in successful)
    total_tokens = sum(r.get("total_tokens", 0) for r in successful)

    return {
        "judge_model": judge_model,
        "rotations_per_concept": rotations,
        "total_concepts": n,
        "failed_concepts": len(results) - n,
        "total_judge_calls": n * rotations,
        "started_at": started_at,
        "finished_at": time.strftime("%Y%m%d_%H%M%S"),
        "total_cost_eur": round(total_cost, 8),
        "total_tokens": total_tokens,
        "win_counts": win_counts,
        "win_rates": {
            arm: round(count / n, 3) for arm, count in win_counts.items()
        },
        "mean_scores": arm_means,
    }


# ---------------------------------------------------------------------------
# JSON encoder
# ---------------------------------------------------------------------------

class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="RQ1 LLM-as-a-Judge: score and rank three evaluation arms"
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Path to the RQ1 V2 run directory containing by_concept.json",
    )
    parser.add_argument(
        "--judge-model",
        default="gpt-4o",
        help="Model to use as judge (default: gpt-4o)",
    )
    parser.add_argument(
        "--rotations",
        type=int,
        default=3,
        help="Number of ordering rotations per concept to cancel position "
             "bias (default: 3)",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=1,
        help="Max concepts to judge in parallel (default: 1)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of concepts judged",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the judge prompt for the first concept and exit",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    by_concept_path = run_dir / "by_concept.json"
    if not by_concept_path.exists():
        raise SystemExit(f"Missing by_concept.json in {run_dir}")

    rows = json.loads(by_concept_path.read_text(encoding="utf-8"))

    # Check if game_text is in by_concept.json; if not, load from DB
    needs_game_text = not rows[0].get("game_text")
    if needs_game_text:
        from game_concept.models import GameConcept

        for row in rows:
            concept_id = row.get("concept_id")
            if concept_id:
                try:
                    concept = GameConcept.objects.get(id=concept_id)
                    row["game_text"] = concept.content
                except GameConcept.DoesNotExist:
                    row["game_text"] = ""

    if args.limit is not None:
        rows = rows[: max(0, args.limit)]

    if not rows:
        raise SystemExit("No concepts to judge.")

    # Dry run: show the prompt for the first concept
    if args.dry_run:
        row = rows[0]
        responses = {
            arm: row[arm]["response"] for arm in ARM_KEYS
            if row[arm].get("response")
        }
        if len(responses) == 3:
            prompt, mapping = _build_anonymized_prompt(
                row.get("game_text", ""), responses, seed=0
            )
            print(f"=== Mapping: {mapping} ===\n")
            print(prompt)
            print(f"\n=== Prompt length: {len(prompt)} chars ===")
        else:
            print("First concept doesn't have all 3 successful responses.")
        return 0

    from llm.logfire_config import get_logfire

    logfire = get_logfire()
    started_at = time.strftime("%Y%m%d_%H%M%S")
    total = len(rows)
    max_parallel = max(1, args.max_parallel)
    rotations = max(1, args.rotations)

    total_calls = total * rotations
    print(
        f"Judging {total} concepts with {args.judge_model}, "
        f"rotations={rotations}, parallel={max_parallel} "
        f"({total_calls} total judge calls)"
    )

    results: List[Dict[str, Any]] = []

    with logfire.span(
        "RQ1 Judge — {total} concepts x {rotations} rotations, "
        "judge={judge_model}",
        total=total,
        rotations=rotations,
        judge_model=args.judge_model,
        max_parallel=max_parallel,
    ):
        if max_parallel == 1:
            for i, row in enumerate(rows):
                print(
                    f"  [{i + 1}/{total}] {row['project_name']}"
                )
                try:
                    result = _judge_concept(
                        concept_row=row,
                        judge_model=args.judge_model,
                        rotations=rotations,
                        index=i + 1,
                        total=total,
                    )
                    results.append(result)
                    if result["success"]:
                        winner = result["ranking"][0]
                        scores = result["scores"]
                        print(
                            f"    Winner: {winner} | "
                            f"mono={scores['monolithic']['total']}/25 "
                            f"full={scores['agentic_full_text']['total']}/25 "
                            f"routed={scores['agentic_routed']['total']}/25"
                        )
                    else:
                        print(f"    SKIP: {result.get('error')}")
                except Exception as exc:
                    logfire.exception(
                        "Judge error for {project_name}: {error}",
                        project_name=row.get("project_name"),
                        error=str(exc),
                    )
                    print(f"    ERROR: {exc}")
        else:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            futures = {}
            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                for i, row in enumerate(rows):
                    print(
                        f"  [{i + 1}/{total}] Queued: {row['project_name']}"
                    )
                    future = executor.submit(
                        _judge_concept,
                        concept_row=row,
                        judge_model=args.judge_model,
                        rotations=rotations,
                        index=i + 1,
                        total=total,
                    )
                    futures[future] = row

                for future in as_completed(futures):
                    row = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        if result["success"]:
                            winner = result["ranking"][0]
                            scores = result["scores"]
                            print(
                                f"  Done: {row['project_name']} | "
                                f"Winner: {winner} | "
                                f"mono={scores['monolithic']['total']}/25 "
                                f"full={scores['agentic_full_text']['total']}/25 "
                                f"routed={scores['agentic_routed']['total']}/25"
                            )
                        else:
                            print(
                                f"  SKIP: {row['project_name']}: "
                                f"{result.get('error')}"
                            )
                    except Exception as exc:
                        logfire.exception(
                            "Judge error for {project_name}: {error}",
                            project_name=row.get("project_name"),
                            error=str(exc),
                        )
                        print(f"  ERROR: {row['project_name']}: {exc}")

    # Build summary
    summary = _build_summary(results, args.judge_model, started_at, rotations)

    # Write output to run directory
    output_dir = run_dir
    (output_dir / "judge_results.json").write_text(
        json.dumps(results, indent=2, cls=_DecimalEncoder) + "\n",
        encoding="utf-8",
    )
    (output_dir / "judge_summary.json").write_text(
        json.dumps(summary, indent=2, cls=_DecimalEncoder) + "\n",
        encoding="utf-8",
    )

    print(f"\nResults saved to {output_dir}/")
    print(f"Judge cost: EUR {summary.get('total_cost_eur', 0):.6f}")
    print(f"Judge calls: {summary.get('total_judge_calls', 0)} "
          f"({rotations} rotations x {summary.get('total_concepts', 0)} concepts)")
    print(f"\n=== Win Rates ===")
    for arm, rate in summary.get("win_rates", {}).items():
        count = summary["win_counts"][arm]
        print(f"  {arm}: {rate:.1%} ({count}/{summary['total_concepts']})")
    print(f"\n=== Mean Scores (out of 25) ===")
    for arm in ARM_KEYS:
        means = summary.get("mean_scores", {}).get(arm, {})
        print(f"  {arm}: {means.get('total', 0):.1f}")
        for d in DIMENSIONS:
            print(f"    {d}: {means.get(d, 0):.2f}")

    # Flush logfire spans
    try:
        logfire.shutdown()
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()
    raise SystemExit(main())
