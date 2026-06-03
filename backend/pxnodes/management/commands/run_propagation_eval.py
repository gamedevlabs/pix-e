"""Evaluate the Change Propagation agent against frozen scenarios.

Loads the dataset into an isolated, throwaway project, runs each scenario under
one or more modes (flat / graph / neighbors), scores flagged affected nodes
against the ground truth, and reports Precision/Recall/F1 (mean ± std). DB writes
are rolled back unless --keep.

Usage:
    python manage.py run_propagation_eval \
        --dataset pxnodes/llm/eval/dataset/anno1404.json \
        --modes flat,graph,neighbors --runs 3
"""

import json
import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pxnodes.llm.eval.change_propagation_runner import load_cp_scenarios, run_cp_eval
from pxnodes.llm.eval.loader import load_dataset

_DEFAULT_GT = (
    Path(__file__).resolve().parents[2]
    / "llm"
    / "eval"
    / "ground_truth"
    / "change_propagation_anno1404.json"
)
_DEFAULT_OUT = Path(__file__).resolve().parents[2] / "llm" / "eval" / "results"
_DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"


class Command(BaseCommand):
    help = "Evaluate the Change Propagation agent against frozen scenarios."

    def add_arguments(self, parser):
        parser.add_argument("--dataset", type=str, required=True)
        parser.add_argument("--ground-truth", type=str, default=str(_DEFAULT_GT))
        parser.add_argument("--modes", type=str, default="flat,graph,neighbors")
        parser.add_argument("--model", type=str, default=_DEFAULT_MODEL)
        parser.add_argument("--runs", type=int, default=3)
        parser.add_argument("--sleep", type=float, default=0.0)
        parser.add_argument("--min-confidence", type=float, default=0.5)
        parser.add_argument("--max-depth", type=int, default=3)
        parser.add_argument(
            "--rag-top-k",
            type=int,
            default=10,
            help="Number of nodes retrieved by the 'semantic' (embedding-RAG) mode.",
        )
        parser.add_argument("--out-dir", type=str, default=str(_DEFAULT_OUT))
        parser.add_argument("--keep", action="store_true")

    def handle(self, *args, **options):
        if not Path(options["dataset"]).exists():
            raise CommandError(f"Dataset not found: {options['dataset']}")

        modes = [m.strip() for m in options["modes"].split(",") if m.strip()]
        scenarios = load_cp_scenarios(options["ground_truth"])
        out_dir = Path(options["out_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = {}

        with transaction.atomic():
            project = load_dataset(options["dataset"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded '{project.name}' ({project.pxnodes.count()} nodes); "
                    f"{len(scenarios)} scenarios"
                )
            )

            for mode in modes:
                runs = 1 if mode == "neighbors" else options["runs"]
                model_note = options["model"] if mode != "neighbors" else "none"
                topk_note = (
                    f", top_k={options['rag_top_k']}" if mode == "semantic" else ""
                )
                self.stdout.write(
                    f"\n========== MODE '{mode}' "
                    f"(runs={runs}, model={model_note}, "
                    f"max_depth={options['max_depth']}{topk_note}) =========="
                )
                report = run_cp_eval(
                    project,
                    scenarios,
                    mode=mode,
                    model_id=options["model"],
                    min_confidence=options["min_confidence"],
                    runs=runs,
                    max_depth=options["max_depth"],
                    semantic_top_k=options["rag_top_k"],
                    inter_run_sleep=options["sleep"],
                )
                self._print_mode(report)
                payload[mode] = self._serialize(report)

            if not options["keep"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("\nRolled back eval project."))

        stamp = time.strftime("%Y%m%d-%H%M%S")
        out_file = out_dir / f"propagation_eval_{stamp}.json"
        out_file.write_text(
            json.dumps(
                {
                    "dataset": options["dataset"],
                    "model": options["model"],
                    "max_depth": options["max_depth"],
                    "min_confidence": options["min_confidence"],
                    "rag_top_k": options["rag_top_k"],
                    "modes": payload,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        self.stdout.write(self.style.SUCCESS(f"\nSaved detailed results → {out_file}"))

    def _print_mode(self, report) -> None:
        f1s = []
        for sr in report.scenarios:
            if sr.metrics is None:
                self.stdout.write(f"  {sr.scenario_id}: all runs failed")
                continue
            m = sr.metrics
            avg_flagged = sum(len(f) for f in sr.flagged_ids) / max(
                1, len(sr.flagged_ids)
            )
            if sr.n_expected == 0:
                # Negative control: P/R/F1 are undefined; restraint = few flags.
                self.stdout.write(
                    f"  {sr.scenario_id} (neg. control): "
                    f"avg {avg_flagged:.1f} nodes flagged "
                    f"(ideal 0); FP/run={m.avg_false_positives:.1f}"
                )
            else:
                f1s.append(m.f1_mean)
                self.stdout.write(
                    f"  {sr.scenario_id}: "
                    f"P={m.precision_mean:.2f}±{m.precision_std:.2f} "
                    f"R={m.recall_mean:.2f}±{m.recall_std:.2f} "
                    f"F1={m.f1_mean:.2f}±{m.f1_std:.2f} "
                    f"(expected {sr.n_expected}, avg flagged {avg_flagged:.1f})"
                )
        if f1s:
            macro = sum(f1s) / len(f1s)
            self.stdout.write(
                self.style.SUCCESS(
                    f"  → macro-F1 over {len(f1s)} scoring scenarios: {macro:.2f}"
                )
            )

        # Feasibility (cost / throughput) averaged per check (= per scenario-run).
        durs = [d for sr in report.scenarios for d in sr.durations_s]
        calls = [c for sr in report.scenarios for c in sr.n_calls]
        ptok = [p for sr in report.scenarios for p in sr.prompt_tokens]
        ctok = [c for sr in report.scenarios for c in sr.completion_tokens]
        if durs:
            avg_lat = sum(durs) / len(durs)
            if calls:
                avg_calls = sum(calls) / len(calls)
                avg_p = sum(ptok) / len(ptok)
                avg_c = sum(ctok) / len(ctok)
                self.stdout.write(
                    f"  ⏱ feasibility/check: {avg_calls:.1f} LLM calls, "
                    f"{avg_p + avg_c:.0f} tokens (prompt {avg_p:.0f} + compl "
                    f"{avg_c:.0f}), {avg_lat:.1f}s"
                )
            else:
                self.stdout.write(
                    f"  ⏱ feasibility/check: no LLM (0 calls / 0 tokens), "
                    f"{avg_lat:.1f}s"
                )

    def _serialize(self, report) -> dict:
        scen = {}
        for sr in report.scenarios:
            entry = {
                "title": sr.title,
                "n_expected": sr.n_expected,
                "flagged_ids": sr.flagged_ids,
                "durations_s": sr.durations_s,
                "n_calls": sr.n_calls,
                "prompt_tokens": sr.prompt_tokens,
                "completion_tokens": sr.completion_tokens,
            }
            if sr.metrics is not None:
                m = sr.metrics
                entry.update(
                    {
                        "precision_mean": m.precision_mean,
                        "precision_std": m.precision_std,
                        "recall_mean": m.recall_mean,
                        "recall_std": m.recall_std,
                        "f1_mean": m.f1_mean,
                        "f1_std": m.f1_std,
                        "avg_false_positives": m.avg_false_positives,
                        "per_run_tp": [[t.id for t in r.tp] for r in sr.run_results],
                        "per_run_fp": [
                            [f.entity_id for f in r.fp] for r in sr.run_results
                        ],
                    }
                )
            scen[sr.scenario_id] = entry
        return {"model_id": report.model_id, "scenarios": scen}
