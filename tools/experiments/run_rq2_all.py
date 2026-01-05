import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path


def _parse_csv(path: Path) -> list[dict[str, str]]:
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
    chart_id: str,
    rows: list[dict[str, str]],
    header: list[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"annotations_{chart_id}.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in header})
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run RQ2 for every chart in a combined annotations CSV."
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
    parser.add_argument(
        "--strategies",
        default="full_context,structural_memory,simple_sm,hierarchical_graph",
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument(
        "--execution-mode",
        choices=["monolithic", "agentic"],
        default="monolithic",
    )
    parser.add_argument("--scope", choices=["global", "node", "all"], default="all")
    parser.add_argument(
        "--node-parallelism",
        type=int,
        default=5,
        help="How many target nodes to evaluate in parallel per strategy.",
    )
    parser.add_argument(
        "--limit-targets",
        type=int,
        default=None,
        help="Limit evaluation to the first N target nodes per chart.",
    )
    parser.add_argument(
        "--skip-reset",
        action="store_true",
        help="Skip cache reset but still run precompute if needed.",
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
        or f"docs/experiments/rq2_combined_{time.strftime('%Y%m%d_%H%M%S')}"
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
        chart_csv = _write_chart_csv(chart_dir, chart_id, chart_rows, header)

        cmd = [
            sys.executable,
            "tools/experiments/run_rq2.py",
            "--chart-id",
            chart_id,
            "--annotations",
            str(chart_csv),
            "--strategies",
            args.strategies,
            "--model",
            args.model,
            "--embedding-model",
            args.embedding_model,
            "--execution-mode",
            args.execution_mode,
            "--scope",
            args.scope,
            "--output-dir",
            str(chart_dir),
            "--node-parallelism",
            str(args.node_parallelism),
        ]
        if args.limit_targets is not None:
            cmd += ["--limit-targets", str(args.limit_targets)]
        if args.skip_reset:
            cmd.append("--skip-reset")

        print(f"Running {chart_label} ({chart_id}) -> {chart_dir}")
        subprocess.run(cmd, check=True)

    print(f"All runs saved under {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
