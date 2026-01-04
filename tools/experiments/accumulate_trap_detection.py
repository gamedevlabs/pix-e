import argparse
import csv
import json
import subprocess
from pathlib import Path


def _read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def _append_rows(source_csv: Path, dest_csv: Path) -> None:
    with source_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        rows = list(reader)

    if not rows:
        return

    if not dest_csv.exists():
        with dest_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(rows)
    else:
        with dest_csv.open("a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)


def _load_chart_id(run_dir: Path) -> str:
    summary_path = run_dir / "summary.json"
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    return str(data.get("chart_id", "")).strip()


def _annotation_csv_for_chart(chart_id: str, combined_csv: Path) -> Path | None:
    with combined_csv.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            if row.get("chart_id", "").strip() == chart_id:
                mission = row.get("mission", "").strip()
                if not mission:
                    return None
                return Path("docs/annotations") / mission / "annotations.csv"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and accumulate trap_detection.csv across multiple runs."
    )
    parser.add_argument(
        "--runs-root",
        required=True,
        help="Root directory containing per-chart run folders.",
    )
    parser.add_argument(
        "--combined-csv",
        default="docs/annotations/annotations_combined.csv",
    )
    parser.add_argument(
        "--output",
        default="docs/experiments/trap_detection_accumulated.csv",
    )
    parser.add_argument(
        "--include-clean",
        action="store_true",
        help="Include clean nodes with no traps.",
    )

    args = parser.parse_args()
    runs_root = Path(args.runs_root)
    combined_csv = Path(args.combined_csv)
    output_csv = Path(args.output)

    if not runs_root.exists():
        raise SystemExit(f"Runs root not found: {runs_root}")
    if not combined_csv.exists():
        raise SystemExit(f"Combined CSV not found: {combined_csv}")

    run_dirs = sorted(
        [p for p in runs_root.iterdir() if p.is_dir() and (p / "summary.json").exists()]
    )
    if not run_dirs:
        raise SystemExit(f"No run directories with summary.json under {runs_root}")

    for run_dir in run_dirs:
        chart_id = _load_chart_id(run_dir)
        if not chart_id:
            raise SystemExit(f"Missing chart_id in {run_dir}/summary.json")

        annotations_csv = _annotation_csv_for_chart(chart_id, combined_csv)
        if not annotations_csv:
            raise SystemExit(f"No annotations CSV for chart {chart_id}")

        cmd = [
            "python",
            "tools/experiments/build_trap_detection.py",
            "--run-dir",
            str(run_dir),
            "--annotations",
            str(annotations_csv),
        ]
        if args.include_clean:
            cmd.append("--include-clean")
        subprocess.run(cmd, check=True)

        trap_csv = run_dir / "trap_detection.csv"
        _append_rows(trap_csv, output_csv)

    print(f"Wrote {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
