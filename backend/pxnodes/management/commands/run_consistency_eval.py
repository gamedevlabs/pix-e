"""Run the automated Consistency-agent evaluation against a frozen dataset.

Loads the dataset into an isolated, throwaway eval project, runs the
Consistency agent N times per layer, scores findings against the ground truth,
and writes a metrics report (mean ± std P/R/F1, per-category recall, false
positives, hallucinations, runtime). DB writes are rolled back afterwards
unless --keep is given.

Usage:
    python manage.py run_consistency_eval \
        --dataset pxnodes/llm/eval/dataset/anno1404.json \
        --layers structural,semantic,all --runs 3
"""

import json
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pxnodes.llm.eval.consistency_runner import load_traps, run_consistency_eval
from pxnodes.llm.eval.loader import load_dataset

_DEFAULT_GT = (
    Path(__file__).resolve().parents[2]
    / "llm"
    / "eval"
    / "ground_truth"
    / "consistency_anno1404.json"
)
_DEFAULT_OUT = Path(__file__).resolve().parents[2] / "llm" / "eval" / "results"
_DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"


class Command(BaseCommand):
    help = "Evaluate the Consistency agent against a frozen ground-truth dataset."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", type=str, required=True)
        parser.add_argument("--ground-truth", type=str, default=str(_DEFAULT_GT))
        parser.add_argument("--layers", type=str, default="structural,semantic,all")
        parser.add_argument("--model", type=str, default=_DEFAULT_MODEL)
        parser.add_argument("--runs", type=int, default=3)
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.0,
            help="Seconds to wait between runs (helps avoid API rate limits).",
        )
        parser.add_argument("--min-confidence", type=float, default=0.0)
        parser.add_argument("--out-dir", type=str, default=str(_DEFAULT_OUT))
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Keep the loaded eval project in the DB (default: roll back).",
        )

    def handle(self, *args, **options):
        dataset = options["dataset"]
        if not Path(dataset).exists():
            raise CommandError(f"Dataset not found: {dataset}")

        layers = [
            layer.strip() for layer in options["layers"].split(",") if layer.strip()
        ]
        out_dir = Path(options["out_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)

        reports_payload = {}

        with transaction.atomic():
            project = load_dataset(dataset)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded '{project.name}' ({project.pxnodes.count()} nodes, "
                    f"{project.pillars.count()} pillars)"
                )
            )

            for layer in layers:
                # Layer 1 is deterministic — a single run suffices.
                runs = 1 if layer == "structural" else options["runs"]
                traps = load_traps(options["ground_truth"], layer)

                self.stdout.write(
                    f"\n=== Layer '{layer}' — {len(traps)} traps, "
                    f"{runs} run(s), model={options['model']} ==="
                )
                report = run_consistency_eval(
                    project,
                    traps,
                    layer=layer,
                    model_id=options["model"] if layer != "structural" else None,
                    min_confidence=options["min_confidence"],
                    runs=runs,
                    inter_run_sleep=options["sleep"],
                )
                if report.metrics is None:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  All {runs} run(s) failed for layer '{layer}' "
                            "(see warnings above) — no metrics."
                        )
                    )
                    continue
                if len(report.run_results) < runs:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Only {len(report.run_results)}/{runs} runs "
                            "succeeded; metrics computed over successful runs."
                        )
                    )
                self._print_report(report)
                reports_payload[layer] = self._serialize(report)

            if not options["keep"]:
                transaction.set_rollback(True)
                self.stdout.write(
                    self.style.WARNING(
                        "\nRolled back eval project (use --keep to retain)."
                    )
                )

        stamp = time.strftime("%Y%m%d-%H%M%S")
        out_file = out_dir / f"consistency_eval_{stamp}.json"
        out_file.write_text(
            json.dumps(
                {
                    "dataset": dataset,
                    "model": options["model"],
                    "min_confidence": options["min_confidence"],
                    "layers": reports_payload,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        self.stdout.write(self.style.SUCCESS(f"\nSaved detailed results → {out_file}"))

    def _print_report(self, report) -> None:
        m = report.metrics
        self.stdout.write(
            f"  Precision: {m.precision_mean:.2f} ± {m.precision_std:.2f}   "
            f"Recall: {m.recall_mean:.2f} ± {m.recall_std:.2f}   "
            f"F1: {m.f1_mean:.2f} ± {m.f1_std:.2f}"
        )
        self.stdout.write(
            f"  Avg false positives: {m.avg_false_positives:.1f}   "
            f"Avg hallucinations: {m.avg_hallucinations:.1f}   "
            f"Avg runtime: {sum(report.durations_s) / len(report.durations_s):.1f}s"
        )
        if m.per_category_recall:
            cats = "  ".join(
                f"{cat}: {rec:.2f}"
                for cat, rec in sorted(m.per_category_recall.items())
            )
            self.stdout.write(f"  Per-category recall: {cats}")

    def _serialize(self, report) -> dict:
        m = report.metrics
        return {
            "layer": report.layer,
            "model_id": report.model_id,
            "min_confidence": report.min_confidence,
            "total_traps": m.total_traps,
            "runs": m.runs,
            "precision_mean": m.precision_mean,
            "precision_std": m.precision_std,
            "recall_mean": m.recall_mean,
            "recall_std": m.recall_std,
            "f1_mean": m.f1_mean,
            "f1_std": m.f1_std,
            "per_category_recall": m.per_category_recall,
            "avg_false_positives": m.avg_false_positives,
            "avg_hallucinations": m.avg_hallucinations,
            "durations_s": report.durations_s,
            "per_run": [
                {
                    "tp": [t.id for t in r.tp],
                    "fn": [t.id for t in r.fn],
                    "fp": [
                        {
                            "category": f.category,
                            "resolved_name": f.resolved_name,
                            "entity_id": f.entity_id,
                        }
                        for f in r.fp
                    ],
                    "hallucinations": [f.entity_id for f in r.hallucinations],
                }
                for r in report.run_results
            ],
            "raw_findings": report.raw_findings,
        }
