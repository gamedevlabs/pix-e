import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _join_list(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value)


def _format_rq1_synthesis(result: Dict[str, Any]) -> str:
    if not result:
        return ""
    parts = []
    parts.append(f"Overall Status: {result.get('overall_status', '')}")
    parts.append(f"Overall Reasoning: {result.get('overall_reasoning', '')}")
    strongest = _join_list(result.get("strongest_aspects"))
    if strongest:
        parts.append(f"Strongest Aspects: {strongest}")
    weakest = _join_list(result.get("weakest_aspects"))
    if weakest:
        parts.append(f"Weakest Aspects: {weakest}")
    critical = _join_list(result.get("critical_gaps"))
    if critical:
        parts.append(f"Critical Gaps: {critical}")
    next_steps = _join_list(result.get("next_steps"))
    if next_steps:
        parts.append(f"Next Steps: {next_steps}")
    consistency = result.get("consistency_notes")
    if consistency:
        parts.append(f"Consistency Notes: {consistency}")
    return "\n".join(parts).strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build LLM-as-a-judge input CSV for RQ1 outputs."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--output",
        default=None,
        help="Output CSV path (default: run-dir/judge_input.csv)",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    by_concept_path = run_dir / "by_concept.json"
    if not by_concept_path.exists():
        raise SystemExit(f"Missing by_concept.json in {run_dir}")

    rows = _load_json(by_concept_path)
    output_path = Path(args.output or (run_dir / "judge_input.csv"))

    fieldnames = [
        "project_id",
        "project_name",
        "concept_id",
        "game_text",
        "monolithic_summary",
        "agentic_full_text_summary",
        "agentic_routed_summary",
        "monolithic_tokens",
        "agentic_full_text_tokens",
        "agentic_routed_tokens",
        "monolithic_time_ms",
        "agentic_full_text_time_ms",
        "agentic_routed_time_ms",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            monolithic = row.get("monolithic", {})
            full_text = row.get("agentic_full_text", {})
            routed = row.get("agentic_routed", {})
            rq1_synth = row.get("rq1_synthesis", {})

            writer.writerow(
                {
                    "project_id": row.get("project_id"),
                    "project_name": row.get("project_name"),
                    "concept_id": row.get("concept_id"),
                    "game_text": row.get("game_text"),
                    "monolithic_summary": _format_rq1_synthesis(
                        rq1_synth.get("monolithic", {})
                    ),
                    "agentic_full_text_summary": _format_rq1_synthesis(
                        rq1_synth.get("agentic_full_text", {})
                    ),
                    "agentic_routed_summary": _format_rq1_synthesis(
                        rq1_synth.get("agentic_routed", {})
                    ),
                    "monolithic_tokens": monolithic.get("total_tokens", 0),
                    "agentic_full_text_tokens": full_text.get("total_tokens", 0),
                    "agentic_routed_tokens": routed.get("total_tokens", 0),
                    "monolithic_time_ms": monolithic.get("execution_time_ms", 0),
                    "agentic_full_text_time_ms": full_text.get("execution_time_ms", 0),
                    "agentic_routed_time_ms": routed.get("execution_time_ms", 0),
                }
            )

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
