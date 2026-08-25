from rest_framework.exceptions import ValidationError

from projects.serializers import ProjectTransferSerializer
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
    PxLockAssignment,
)
from pxnodes.models import (
    PxComponent,
    PxComponentDefinition,
    PxKeyAssignment,
    PxKeyDefinition,
    PxLockDefinition,
    PxNode,
)

SUPPORTED_VERSION = 1


def overwrite_project_data(project, payload, user):
    """Replace `project`'s child data with the merged desired state in `payload`.

    The payload is the export-shaped full state the diff viewer produced (NEW
    inserted, MODIFIED taking the file version, DELETED already removed,
    UNCHANGED kept). Ids from the payload are preserved so re-export round-trips.
    Runs inside the caller's transaction.
    """
    version = payload.get("version")
    if version != SUPPORTED_VERSION:
        raise ValidationError(f"Unsupported export version: {version}")

    project_data = payload.get("project")
    if not project_data:
        raise ValidationError("Missing project data.")

    # ponytail: project id is match-only; never let a payload reassign the pk.
    serializer = ProjectTransferSerializer(project, data=project_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Key/lock definitions are owner-scoped and shared across projects, so we
    # upsert by id instead of delete+recreate (deleting could hit other projects).
    for d in payload.get("px_key_definitions", []):
        PxKeyDefinition.objects.update_or_create(
            id=d["id"],
            owner=user,
            defaults={
                "name": d["name"],
                "key_type": d["key_type"],
                "consumable": d["consumable"],
                "fixed": d["fixed"],
                "unique": d["unique"],
            },
        )

    lock_defs = payload.get("px_lock_definitions", [])
    for d in lock_defs:
        PxLockDefinition.objects.update_or_create(
            id=d["id"],
            owner=user,
            defaults={
                "name": d["name"],
                "soft_gate": d["soft_gate"],
                "unlock_mode": d["unlock_mode"],
            },
        )
    for d in lock_defs:
        PxLockDefinition.objects.get(id=d["id"]).unlocked_by.set(d.get("unlocked_by", []))

    # Wipe project-scoped rows. Deleting charts cascades containers, layouts,
    # edges and lock assignments; deleting nodes cascades components and key
    # assignments.
    PxChart.objects.filter(project=project).delete()
    PxNode.objects.filter(project=project).delete()
    PxComponentDefinition.objects.filter(project=project).delete()

    _require_referenced(payload)

    for d in payload.get("px_component_definitions", []):
        PxComponentDefinition.objects.create(
            id=d["id"],
            name=d["name"],
            type=d["type"],
            owner=user,
            project=project,
        )

    for d in payload.get("px_nodes", []):
        PxNode.objects.create(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            owner=user,
            project=project,
        )

    for d in payload.get("px_components", []):
        PxComponent.objects.create(
            id=d["id"],
            node_id=d["node"],
            definition_id=d["definition"],
            value=d["value"],
            owner=user,
        )

    # Key assignments are exported owner-wide (not just this project), so a
    # payload may carry rows belonging to other projects; upsert to avoid pk
    # collisions with rows the cascade above didn't touch.
    for d in payload.get("px_key_assignments", []):
        PxKeyAssignment.objects.update_or_create(
            id=d["id"],
            defaults={
                "count": d["count"],
                "node_id": d["node"],
                "definition_id": d["definition"],
                "owner": user,
            },
        )

    for d in payload.get("px_charts", []):
        PxChart.objects.create(
            id=d["id"],
            name=d["name"],
            description=d["description"],
            associatedNode_id=d.get("associatedNode"),
            project=project,
            owner=user,
        )

    for d in payload.get("px_chart_containers", []):
        PxChartContainer.objects.create(
            id=d["id"],
            name=d["name"],
            px_chart_id=d["px_chart"],
            content_id=d.get("content"),
            owner=user,
        )

    # Containers auto-get a default layout via a post_save signal, so update
    # that row instead of inserting (which would hit the OneToOne constraint).
    for d in payload.get("px_chart_container_layouts", []):
        PxChartContainerLayout.objects.update_or_create(
            container_id=d["container"],
            defaults={
                "position_x": d["position_x"],
                "position_y": d["position_y"],
                "width": d["width"],
                "height": d["height"],
            },
        )

    for d in payload.get("px_chart_edges", []):
        PxChartEdge.objects.create(
            id=d["id"],
            sourceHandle=d["sourceHandle"],
            targetHandle=d["targetHandle"],
            bidirectional=d["bidirectional"],
            source_id=d["source"],
            target_id=d["target"],
            px_chart_id=d["px_chart"],
            owner=user,
        )

    for d in payload.get("px_lock_assignments", []):
        PxLockAssignment.objects.create(
            id=d["id"],
            count=d["count"],
            definition_id=d["definition"],
            edge_id=d["edge"],
            px_chart_id=d["px_chart"],
            owner=user,
        )

    return project


def _require_referenced(payload):
    """Block apply if a row references an id not present in the merged payload.

    The frontend auto-includes dependencies, but this guards against a caller
    (or a hand-edited file) sending a component whose node/definition was cut.
    """
    # Ids may arrive as UUID objects or strings depending on the caller, so
    # compare everything as strings.
    def ids(key):
        return {str(d["id"]) for d in payload.get(key, [])}

    node_ids = ids("px_nodes")
    def_ids = ids("px_component_definitions")
    chart_ids = ids("px_charts")
    container_ids = ids("px_chart_containers")

    def check(cond, msg):
        if not cond:
            raise ValidationError(msg)

    for d in payload.get("px_components", []):
        check(str(d["node"]) in node_ids, f"Component {d['id']} references a missing node.")
        check(
            str(d["definition"]) in def_ids,
            f"Component {d['id']} references a missing definition.",
        )
    for d in payload.get("px_chart_containers", []):
        check(
            str(d["px_chart"]) in chart_ids,
            f"Container {d['id']} references a missing chart.",
        )
    for d in payload.get("px_chart_edges", []):
        check(
            str(d["source"]) in container_ids and str(d["target"]) in container_ids,
            f"Edge {d['id']} references a missing container.",
        )
    for d in payload.get("px_chart_container_layouts", []):
        check(
            str(d["container"]) in container_ids,
            f"Layout references a missing container ({d['container']}).",
        )
