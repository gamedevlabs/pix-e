import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        return [row for row in reader]


def _parse_list(value: str) -> list[str]:
    raw = (value or "").strip()
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            pass
    if "|" in raw:
        return [part.strip() for part in raw.split("|") if part.strip()]
    return [raw]


def _explode_traps(row: dict[str, str]) -> list[dict[str, str]]:
    fields = [
        "trap_type",
        "mpip",
        "expected_outcome",
        "expected_dimension",
        "expected_evidence",
        "notes",
    ]
    values = {}
    for field in fields:
        if field == "expected_evidence":
            values[field] = [row.get(field, "")]
        else:
            values[field] = _parse_list(row.get(field, ""))
    max_len = max((len(v) for v in values.values()), default=0)

    if max_len == 0:
        return []

    exploded = []
    for i in range(max_len):
        entry = dict(row)
        for field in fields:
            items = values[field]
            entry[field] = items[i] if i < len(items) else ""
        exploded.append(entry)
    return exploded


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _dimension_fields(dimensions: dict[str, Any], prefix: str) -> dict[str, str]:
    dim = dimensions.get(prefix, {}) if isinstance(dimensions, dict) else {}
    return {
        f"{prefix}_score": _stringify(dim.get("score")),
        f"{prefix}_issues": _stringify(dim.get("issues")),
        f"{prefix}_reasoning": _stringify(dim.get("reasoning")),
        f"{prefix}_evidence": _stringify(dim.get("evidence")),
    }


def _iter_detection_rows(
    annotations: list[dict[str, str]],
    results: list[dict[str, Any]],
    run_meta: dict[str, Any],
    include_clean: bool,
) -> Iterable[dict[str, str]]:
    results_by_node: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        node_id = str(result.get("node_id", ""))
        if node_id:
            results_by_node.setdefault(node_id, []).append(result)

    for row in annotations:
        node_id = row.get("node_id", "")
        node_title = row.get("node_title", "")
        traps = _explode_traps(row)
        if not traps and not include_clean:
            continue
        if not traps:
            traps = [dict(row)]

        for trap in traps:
            for result in results_by_node.get(node_id, []):
                dimensions = result.get("dimensions", {})
                base = {
                    "run_id": run_meta.get("run_id", ""),
                    "chart_id": run_meta.get("chart_id", ""),
                    "chart_name": run_meta.get("chart_name", ""),
                    "execution_mode": run_meta.get("execution_mode", ""),
                    "model": run_meta.get("model", ""),
                    "temperature": _stringify(run_meta.get("temperature", 0)),
                    "strategy": result.get("strategy", ""),
                    "node_id": node_id,
                    "node_title": node_title,
                    "trap_type": trap.get("trap_type", ""),
                    "mpip": trap.get("mpip", ""),
                    "expected_outcome": trap.get("expected_outcome", ""),
                    "expected_dimension": trap.get("expected_dimension", ""),
                    "expected_evidence": trap.get("expected_evidence", ""),
                    "annotation_notes": trap.get("notes", ""),
                    "detected": "",
                    "evidence_match": "",
                    "reviewer_notes": "",
                }

                base.update(_dimension_fields(dimensions, "backward_coherence"))
                base.update(_dimension_fields(dimensions, "forward_coherence"))
                base.update(_dimension_fields(dimensions, "global_fit"))
                base.update(_dimension_fields(dimensions, "node_integrity"))
                base["overall_score"] = _stringify(result.get("overall_score"))
                base["total_tokens"] = _stringify(result.get("total_tokens"))
                base["execution_time_ms"] = _stringify(
                    result.get("execution_time_ms")
                )
                yield base


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build trap detection CSV from RQ2 results and annotations."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--include-clean", action="store_true")

    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    annotations_path = Path(args.annotations)

    by_node_path = run_dir / "by_node.json"
    summary_path = run_dir / "summary.json"
    if not by_node_path.exists():
        raise SystemExit(f"Missing by_node.json in {run_dir}")
    if not summary_path.exists():
        raise SystemExit(f"Missing summary.json in {run_dir}")

    results = _load_json(by_node_path)
    run_meta = _load_json(summary_path)
    run_meta["run_id"] = run_dir.name
    annotations = _parse_csv(annotations_path)

    rows = list(
        _iter_detection_rows(
            annotations=annotations,
            results=results,
            run_meta=run_meta,
            include_clean=args.include_clean,
        )
    )
    if not rows:
        raise SystemExit("No rows generated. Check inputs.")

    output_path = run_dir / "trap_detection.csv"
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
