"""Re-score a saved consistency eval result with the current matching logic.

The eval harness persists every run's raw findings, so a matching fix can be
applied retroactively — recomputing Precision/Recall/F1 from saved data with
**no new LLM calls**. Pure file operation: no database, no model access.

Usage:
    python manage.py rescore_consistency_eval \
        --results pxnodes/llm/eval/results/consistency_eval_20260603-083906.json \
        --dataset pxnodes/llm/eval/dataset/anno1404.json
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from pxnodes.llm.eval.consistency_runner import load_traps, to_finding
from pxnodes.llm.eval.metrics import aggregate, match_run

_DEFAULT_GT = (
    Path(__file__).resolve().parents[2]
    / "llm"
    / "eval"
    / "ground_truth"
    / "consistency_anno1404.json"
)


class Command(BaseCommand):
    help = "Re-score a saved consistency eval result (no LLM calls)."

    def add_arguments(self, parser):
        parser.add_argument("--results", type=str, required=True)
        parser.add_argument("--dataset", type=str, required=True)
        parser.add_argument("--ground-truth", type=str, default=str(_DEFAULT_GT))

    def handle(self, *args, **options):
        for key in ("results", "dataset"):
            if not Path(options[key]).exists():
                raise CommandError(f"{key} file not found: {options[key]}")

        results = json.loads(Path(options["results"]).read_text())
        dataset = json.loads(Path(options["dataset"]).read_text())
        node_map = {str(n["id"]): n["name"] for n in dataset["pxnodes"]}

        self.stdout.write(
            f"Re-scoring {Path(options['results']).name} "
            f"({len(node_map)} nodes in dataset)\n"
        )

        for layer, payload in results.get("layers", {}).items():
            raw_runs = payload.get("raw_findings", [])
            if not raw_runs:
                continue
            traps = load_traps(options["ground_truth"], layer)

            run_results = []
            for raw in raw_runs:
                findings = [
                    to_finding(f["category"], f["entity_id"], f["message"], node_map)
                    for f in raw
                ]
                run_results.append(match_run(findings, traps))

            m = aggregate(run_results, traps)
            self.stdout.write(
                f"=== Layer '{layer}' — {m.total_traps} traps, {m.runs} run(s) ==="
            )
            self.stdout.write(
                f"  Precision: {m.precision_mean:.2f} ± {m.precision_std:.2f}   "
                f"Recall: {m.recall_mean:.2f} ± {m.recall_std:.2f}   "
                f"F1: {m.f1_mean:.2f} ± {m.f1_std:.2f}"
            )
            self.stdout.write(
                f"  Avg false positives: {m.avg_false_positives:.1f}   "
                f"Avg hallucinations: {m.avg_hallucinations:.1f}"
            )
            if m.per_category_recall:
                cats = "  ".join(
                    f"{c}: {r:.2f}" for c, r in sorted(m.per_category_recall.items())
                )
                self.stdout.write(f"  Per-category recall: {cats}")
            self.stdout.write("")
