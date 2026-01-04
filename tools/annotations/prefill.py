import csv
import json
import os
import sys
import uuid
from collections import defaultdict
from pathlib import Path

import django

def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python tools/annotations/prefill.py <chart_id> <annotations.csv> <annotations.json>"
        )
        return 1

    chart_id_raw = sys.argv[1]
    csv_path = Path(sys.argv[2])
    json_path = Path(sys.argv[3])

    backend_root = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()

    from pxcharts.models import PxChart, PxChartEdge
    from pxnodes.models import PxNode

    try:
        try:
            chart_id = uuid.UUID(chart_id_raw)
        except ValueError:
            chart_id = uuid.UUID(hex=chart_id_raw)
        chart = PxChart.objects.get(id=chart_id)
    except Exception as exc:
        print(f"Chart not found: {chart_id_raw} ({exc})")
        return 1

    containers = list(chart.containers.select_related("content").all())
    container_by_id = {str(c.id): c for c in containers}

    nodes = []
    for container in containers:
        node = container.content
        if not node:
            continue
        nodes.append(node)

    node_by_id = {str(n.id): n for n in nodes}

    incoming = defaultdict(list)
    outgoing = defaultdict(list)

    edges = list(PxChartEdge.objects.filter(px_chart=chart))
    for edge in edges:
        source = container_by_id.get(str(edge.source_id))
        target = container_by_id.get(str(edge.target_id))
        source_node = getattr(source, "content", None) if source else None
        target_node = getattr(target, "content", None) if target else None
        source_label = getattr(source_node, "name", None) or getattr(source, "name", "")
        target_label = getattr(target_node, "name", None) or getattr(target, "name", "")
        if source_node:
            outgoing[str(source_node.id)].append(target_label)
        if target_node:
            incoming[str(target_node.id)].append(source_label)

    node_rows = []
    for node in nodes:
        components = []
        for comp in node.components.select_related("definition").all():
            def_name = getattr(comp.definition, "name", "")
            components.append(f"{def_name}={comp.value}")
        node_rows.append(
            {
                "node_id": str(node.id),
                "node_title": node.name,
                "node_description": (node.description or "").replace("\n", " ").strip(),
                "components": json.dumps(components, ensure_ascii=True),
                "incoming_nodes": json.dumps(incoming.get(str(node.id), []), ensure_ascii=True),
                "outgoing_nodes": json.dumps(outgoing.get(str(node.id), []), ensure_ascii=True),
                "trap_type": "",
                "mpip": "",
                "expected_outcome": "",
                "expected_dimension": "",
                "expected_evidence": json.dumps([], ensure_ascii=True),
                "notes": "",
                "is_target": "false",
            }
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "node_id",
                "node_title",
                "node_description",
                "components",
                "incoming_nodes",
                "outgoing_nodes",
                "trap_type",
                "mpip",
                "expected_outcome",
                "expected_dimension",
                "expected_evidence",
                "notes",
                "is_target",
            ],
        )
        writer.writeheader()
        for row in node_rows:
            writer.writerow(row)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    if json_path.exists():
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data.update(
        {
            "chart_id": str(chart.id),
            "chart_name": chart.name,
            "version": data.get("version", "v1"),
            "nodes": [
                {
                    "node_id": row["node_id"],
                    "node_title": row["node_title"],
                    "node_description": row["node_description"],
                    "components": json.loads(row["components"]) if row["components"] else [],
                    "incoming_nodes": json.loads(row["incoming_nodes"]) if row["incoming_nodes"] else [],
                    "outgoing_nodes": json.loads(row["outgoing_nodes"]) if row["outgoing_nodes"] else [],
                }
                for row in node_rows
            ],
            "edges": [
                {
                    "source": str(edge.source_id),
                    "target": str(edge.target_id),
                    "source_handle": edge.sourceHandle,
                    "target_handle": edge.targetHandle,
                }
                for edge in edges
            ],
            "targets": data.get("targets", []),
        }
    )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
        f.write("\n")

    print(f"Wrote {len(node_rows)} nodes to {csv_path}")
    print(f"Updated {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
