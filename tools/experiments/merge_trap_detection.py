import argparse
import csv
from pathlib import Path


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge updated trap_detection.csv rows into a combined file."
    )
    parser.add_argument("--combined", required=True)
    parser.add_argument(
        "--update",
        action="append",
        required=True,
        help="Path to trap_detection.csv with updated rows (repeatable).",
    )

    args = parser.parse_args()
    combined_path = Path(args.combined)
    if not combined_path.exists():
        raise SystemExit(f"Combined CSV not found: {combined_path}")

    combined_header, combined_rows = _read_csv(combined_path)
    if not combined_header:
        raise SystemExit(f"Empty combined CSV: {combined_path}")

    update_rows: list[dict[str, str]] = []
    update_keys: set[tuple[str, str]] = set()

    for update_path_str in args.update:
        update_path = Path(update_path_str)
        if not update_path.exists():
            raise SystemExit(f"Update CSV not found: {update_path}")
        _, rows = _read_csv(update_path)
        for row in rows:
            node_id = row.get("node_id", "").strip()
            strategy = row.get("strategy", "").strip()
            if node_id and strategy:
                update_keys.add((node_id, strategy))
                update_rows.append(row)

    if not update_keys:
        raise SystemExit("No update rows found.")

    filtered = [
        row
        for row in combined_rows
        if (row.get("node_id", "").strip(), row.get("strategy", "").strip())
        not in update_keys
    ]

    filtered.extend(update_rows)

    with combined_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=combined_header)
        writer.writeheader()
        for row in filtered:
            writer.writerow({key: row.get(key, "") for key in combined_header})

    print(f"Updated {combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
