import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path


def _parse_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        return list(reader), list(reader.fieldnames or [])


def _slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "chart"


def _write_chart_csv(
    output_dir: Path,
    rows: list[dict[str, str]],
    header: list[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "annotations.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})
    return out_path


def _merge_outputs(output_dir: Path, group_dirs: list[Path]) -> None:
    by_node = []
    by_strategy = []
    summary = None

    for group_dir in group_dirs:
        by_node_path = group_dir / "by_node.json"
        by_strategy_path = group_dir / "by_strategy.csv"
        summary_path = group_dir / "summary.json"

        if by_node_path.exists():
            by_node.extend(json.loads(by_node_path.read_text(encoding="utf-8")))
        if by_strategy_path.exists():
            with by_strategy_path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                by_strategy.extend(list(reader))
        if summary is None and summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

    if summary is None:
        raise SystemExit(f"No summary.json found in {group_dirs}")

    summary["strategies"] = [
        "simple_sm",
        "structural_memory",
        "hierarchical_graph",
        "hmem",
    ]
    summary["dimensions_by_strategy"] = {
        "simple_sm": ["global_fit", "node_integrity"],
        "structural_memory": ["global_fit", "node_integrity"],
        "hierarchical_graph": ["backward_coherence", "forward_coherence"],
        "hmem": ["backward_coherence", "forward_coherence"],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "by_node.json").write_text(
        json.dumps(by_node, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    if by_strategy:
        with (output_dir / "by_strategy.csv").open(
            "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=list(by_strategy[0].keys()))
            writer.writeheader()
            writer.writerows(by_strategy)

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run selected subagents per strategy across charts."
    )
    parser.add_argument(
        "--combined-csv",
        default="docs/annotations/annotations_combined.csv",
    )
    parser.add_argument(
        "--output-root",
        default=None,
        help="Root directory for per-chart outputs.",
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument(
        "--execution-mode",
        choices=["agentic"],
        default="agentic",
    )
    parser.add_argument("--scope", choices=["global", "node", "all"], default="all")
    parser.add_argument(
        "--node-parallelism",
        type=int,
        default=5,
        help="How many target nodes to evaluate in parallel per strategy.",
    )
    parser.add_argument(
        "--skip-precompute",
        action="store_true",
        help="Skip cache reset and precompute (reuse existing cache).",
    )
    parser.add_argument(
        "--limit-targets",
        type=int,
        default=None,
        help="Limit evaluation to the first N target nodes per chart.",
    )

    args = parser.parse_args()
    combined_path = Path(args.combined_csv)
    if not combined_path.exists():
        raise SystemExit(f"Combined CSV not found: {combined_path}")

    rows, header = _parse_csv(combined_path)
    if "chart_id" not in header:
        raise SystemExit("Combined CSV must include chart_id column.")

    output_root = Path(
        args.output_root
        or f"docs/experiments/rq2_subagents_{time.strftime('%Y%m%d_%H%M%S')}"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict[str, str]]] = {}
    chart_names: dict[str, str] = {}
    for row in rows:
        chart_id = (row.get("chart_id") or "").strip()
        if not chart_id:
            continue
        grouped.setdefault(chart_id, []).append(row)
        chart_names.setdefault(chart_id, row.get("chart_name", "").strip())

    if not grouped:
        raise SystemExit("No chart_id rows found in combined CSV.")

    for chart_id, chart_rows in grouped.items():
        chart_label = chart_names.get(chart_id) or chart_id
        chart_slug = _slug(chart_label)
        chart_dir = output_root / f"{chart_slug}_{chart_id[:8]}"
        chart_csv = _write_chart_csv(chart_dir, chart_rows, header)

        group_a_dir = chart_dir / "sm_subset"
        group_b_dir = chart_dir / "graph_hmem_subset"

        base_cmd = [
            sys.executable,
            "tools/experiments/run_rq2.py",
            "--chart-id",
            chart_id,
            "--annotations",
            str(chart_csv),
            "--model",
            args.model,
            "--embedding-model",
            args.embedding_model,
            "--execution-mode",
            args.execution_mode,
            "--scope",
            args.scope,
            "--node-parallelism",
            str(args.node_parallelism),
        ]
        if args.skip_precompute:
            base_cmd.append("--skip-precompute")
        if args.limit_targets is not None:
            base_cmd += ["--limit-targets", str(args.limit_targets)]

        cmd_a = base_cmd + [
            "--strategies",
            "simple_sm,structural_memory",
            "--dimensions",
            "global_fit,node_integrity",
            "--output-dir",
            str(group_a_dir),
        ]
        cmd_b = base_cmd + [
            "--strategies",
            "hierarchical_graph,hmem",
            "--dimensions",
            "backward_coherence,forward_coherence",
            "--output-dir",
            str(group_b_dir),
        ]

        print(f"Running {chart_label} ({chart_id})")
        subprocess.run(cmd_a, check=True)
        subprocess.run(cmd_b, check=True)

        _merge_outputs(chart_dir, [group_a_dir, group_b_dir])

    print(f"All runs saved under {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
