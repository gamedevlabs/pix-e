import argparse
import csv
import json
import os
import sys
import uuid
from pathlib import Path

import django
import logfire


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


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


def _resolve_chart(chart_id_raw: str):
    from pxcharts.models import PxChart

    try:
        try:
            chart_id = uuid.UUID(chart_id_raw)
        except ValueError:
            chart_id = uuid.UUID(hex=chart_id_raw)
        return PxChart.objects.get(id=chart_id)
    except Exception as exc:
        raise SystemExit(f"Chart not found: {chart_id_raw} ({exc})")


def _should_apply(row: dict[str, str], mode: str) -> bool:
    if mode == "all":
        return True
    if mode == "targets":
        return _is_truthy(row.get("is_target", ""))
    if mode == "traps":
        return any(
            (row.get(field) or "").strip()
            for field in (
                "trap_type",
                "mpip",
                "expected_outcome",
                "expected_dimension",
                "expected_evidence",
                "notes",
            )
        )
    return False


def _parse_components(raw: str) -> list[str]:
    if not raw:
        return []
    raw = raw.strip()
    normalized = (
        raw.replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .replace("‘", "'")
    )
    if normalized.startswith("[") and normalized.endswith("]"):
        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            inner = normalized[1:-1]
            reader = csv.reader([inner], delimiter=",", quotechar='"')
            items = next(reader, [])
            return [item.strip() for item in items if item.strip()]
    if "|" in raw:
        return [part.strip() for part in raw.split("|") if part.strip()]
    return [normalized]


def _coerce_value(value: str, comp_type: str):
    raw = value.strip()
    if comp_type == "boolean":
        return raw.lower() in {"true", "1", "yes", "y"}
    if comp_type == "number":
        try:
            if "." in raw:
                return float(raw)
            return int(raw)
        except ValueError:
            return raw
    return raw


def _resolve_node(chart, node_id: str, node_title: str | None):
    container = (
        chart.containers.select_related("content")
        .filter(content_id=node_id)
        .first()
    )
    if container and container.content:
        return container.content

    if node_title:
        container = (
            chart.containers.select_related("content")
            .filter(content__name=node_title)
            .first()
        )
        if container and container.content:
            logfire.warning(
                "apply_traps.node_id_not_in_chart_using_title_match",
                node_id=node_id,
                node_title=node_title,
                chart_id=str(chart.id),
            )
            return container.content

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply annotation edits to chart nodes."
    )
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument(
        "--filter",
        choices=["targets", "traps", "all"],
        default="targets",
        help="Which CSV rows to apply.",
    )
    parser.add_argument(
        "--update-components",
        action="store_true",
        help="Update components from CSV components column.",
    )
    parser.add_argument(
        "--create-components",
        action="store_true",
        help="Create missing components when updating.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log changes without saving.",
    )
    parser.add_argument(
        "--debug-components",
        action="store_true",
        help="Log parsed components and definition matches.",
    )
    parser.add_argument(
        "--create-definitions",
        action="store_true",
        help="Create missing component definitions when needed.",
    )

    args = parser.parse_args()

    chart = _resolve_chart(args.chart_id)
    rows = _parse_csv(Path(args.annotations))

    from pxnodes.models import PxComponent, PxComponentDefinition

    definition_cache = {
        d.name: d for d in PxComponentDefinition.objects.all()
    }

    total_rows = 0
    matched_rows = 0
    updated_nodes = 0
    skipped_missing = 0
    changes = []

    for row in rows:
        total_rows += 1
        if not _should_apply(row, args.filter):
            continue
        matched_rows += 1

        node_id = (row.get("node_id") or "").strip()
        node_title = (row.get("node_title") or "").strip()
        if not node_id and not node_title:
            continue

        node = _resolve_node(chart, node_id, node_title)
        if not node:
            skipped_missing += 1
            logfire.warning(
                "apply_traps.node_not_found_in_chart",
                node_id=node_id,
                node_title=node_title,
                chart_id=str(chart.id),
            )
            continue

        node_changes = []
        new_title = (row.get("node_title") or "").strip()
        new_description = (row.get("node_description") or "").strip()

        if new_title and new_title != node.name:
            node_changes.append(("name", node.name, new_title))
            if not args.dry_run:
                node.name = new_title

        if new_description and new_description != (node.description or ""):
            node_changes.append(("description", node.description, new_description))
            if not args.dry_run:
                node.description = new_description

        if args.update_components:
            entries = _parse_components(row.get("components", ""))
            for entry in entries:
                if "=" not in entry:
                    continue
                comp_name, comp_value = entry.split("=", 1)
                comp_name = comp_name.strip()
                comp_value = comp_value.strip()
                if not comp_name:
                    continue
                definition = definition_cache.get(comp_name)
                if not definition:
                    if args.create_definitions:
                        if args.debug_components:
                            print(
                                f"[components] creating definition for '{comp_name}'"
                                f" on node {node.name} ({node.id})"
                            )
                        if not args.dry_run:
                            definition = PxComponentDefinition.objects.create(
                                id=uuid.uuid4(),
                                name=comp_name,
                                type="string",
                                owner=node.owner,
                                project=node.project,
                            )
                            definition_cache[comp_name] = definition
                        else:
                            definition = PxComponentDefinition(
                                id=uuid.uuid4(),
                                name=comp_name,
                                type="string",
                                owner=node.owner,
                                project=node.project,
                            )
                            definition_cache[comp_name] = definition
                            node_changes.append(
                                (f"component_def:{comp_name}", None, "string")
                            )
                    else:
                        if args.debug_components:
                            print(
                                f"[components] missing definition for '{comp_name}'"
                                f" on node {node.name} ({node.id})"
                            )
                        logfire.warning(
                            "apply_traps.component_definition_missing",
                            component_name=comp_name,
                            node_id=str(node.id),
                        )
                        continue
                if args.debug_components and definition:
                    print(
                        f"[components] matched '{comp_name}' ({definition.type})"
                        f" on node {node.name} ({node.id})"
                    )
                coerced_value = _coerce_value(comp_value, definition.type)
                component = (
                    PxComponent.objects.filter(node=node, definition=definition)
                    .first()
                )
                if component:
                    if component.value != coerced_value:
                        node_changes.append(
                            (f"component:{comp_name}", component.value, coerced_value)
                        )
                        if not args.dry_run:
                            component.value = coerced_value
                            component.save(update_fields=["value", "updated_at"])
                elif args.create_components:
                    node_changes.append(
                        (f"component:{comp_name}", None, coerced_value)
                    )
                    if not args.dry_run:
                        PxComponent.objects.create(
                            id=uuid.uuid4(),
                            node=node,
                            definition=definition,
                            value=coerced_value,
                            owner=node.owner,
                        )

        if node_changes:
            updated_nodes += 1
            changes.append((str(node.id), node.name, node_changes))
            if not args.dry_run:
                node.save(update_fields=["name", "description", "updated_at"])

    print(f"Rows scanned: {total_rows}")
    print(f"Rows matched: {matched_rows}")
    print(f"Nodes updated: {updated_nodes}")
    print(f"Nodes missing in chart: {skipped_missing}")

    if args.dry_run and changes:
        print("Planned changes:")
        for node_id, title, node_changes in changes:
            print(f"- {title} ({node_id})")
            for field, old, new in node_changes:
                print(f"  - {field}: {old!r} -> {new!r}")

    return 0


if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()
    raise SystemExit(main())
