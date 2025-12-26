import csv
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python tools/annotations/sync.py <annotations.csv> <annotations.json>")
        return 1

    csv_path = Path(sys.argv[1])
    json_path = Path(sys.argv[2])

    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1
    if not json_path.exists():
        print(f"JSON not found: {json_path}")
        return 1

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    def parse_array(cell: str) -> list[str]:
        if not cell:
            return []
        try:
            value = json.loads(cell)
            return value if isinstance(value, list) else []
        except json.JSONDecodeError:
            return [item.strip() for item in cell.split("|") if item.strip()]

    targets = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            if not row.get("node_id"):
                continue
            targets.append(
                {
                    "node_id": row.get("node_id", "").strip(),
                    "node_title": row.get("node_title", "").strip(),
                    "trap_type": row.get("trap_type", "").strip(),
                    "mpip": row.get("mpip", "").strip(),
                    "expected_outcome": row.get("expected_outcome", "").strip(),
                    "expected_dimension": row.get("expected_dimension", "").strip(),
                    "expected_evidence": parse_array(row.get("expected_evidence", "")),
                    "notes": row.get("notes", "").strip(),
                    "is_target": row.get("is_target", "").strip().lower()
                    in {"true", "1", "yes", "y"},
                }
            )

    data["targets"] = targets
    if "nodes" in data:
        nodes_by_id = {str(node.get("node_id")): node for node in data["nodes"]}
        for row in targets:
            node = nodes_by_id.get(row["node_id"])
            if not node:
                continue
            node["node_title"] = row.get("node_title", "")
            node["node_description"] = row.get("node_description", "")
            node["components"] = parse_array(row.get("components", ""))
            node["incoming_nodes"] = parse_array(row.get("incoming_nodes", ""))
            node["outgoing_nodes"] = parse_array(row.get("outgoing_nodes", ""))

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")

    print(f"Synced {len(targets)} targets -> {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
