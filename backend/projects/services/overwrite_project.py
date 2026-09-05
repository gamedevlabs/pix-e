from rest_framework.exceptions import ValidationError

from game_concept.models import GameConcept
from pillars.models import Pillar
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


def overwrite_project_data(project, payload, user):
    """Replace `project`'s child data with the merged desired state in `payload`.

    The payload is the export-shaped full state the diff viewer produced (NEW
    inserted, MODIFIED taking the file version, DELETED already removed,
    UNCHANGED kept). Ids from the payload are preserved so re-export round-trips.
    Runs inside the caller's transaction.
    """
    project_data = payload.get("project")
    if not project_data:
        raise ValidationError("Missing project data.")

    # ponytail: project id is match-only; never let a payload reassign the pk.
    serializer = ProjectTransferSerializer(project, data=project_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    # Pillars and the concept are rebuilt, not upserted. Their ids are DB-local
    # autoincrement ints with no meaning outside this database - the same reason
    # px_chart_container_layouts[].id must never be keyed on - so honouring an id
    # from the payload would either collide with another project's row or invent
    # a false identity. The merged payload is the desired final state, so the set
    # is replaced wholesale and new ids are issued.
    #
    # Absent means "the client did not send them", which is not the same as an
    # empty list meaning "the user removed them all". Only touch what was sent;
    # an older client that knows nothing about pillars must not wipe them.
    if "pillars" in payload:
        Pillar.objects.filter(project=project).delete()
        for d in payload["pillars"]:
            Pillar.objects.create(
                user=user,
                project=project,
                name=d["name"],
                description=d["description"],
            )

    if "game_concept" in payload:
        concept = payload["game_concept"]
        current = GameConcept.objects.filter(project=project, is_current=True).first()

        # Only the current concept is exported; the history behind it is not, so
        # it must not be destroyed either. Demote rather than delete, and skip
        # entirely when the content already matches - otherwise re-importing the
        # same file piles up an identical row every time.
        if concept is None or current is None or current.content != concept["content"]:
            if current is not None:
                # The one_current_concept_per_project constraint means the old
                # current has to step down before the new one can be created.
                current.is_current = False
                current.save(update_fields=["is_current"])

            if concept:
                GameConcept.objects.create(
                    user=user,
                    project=project,
                    content=concept["content"],
                    is_current=True,
                )

    # Key/lock definitions are project-scoped now, but still upserted by id
    # rather than delete+recreate so that lock assignments referencing them
    # survive the wipe below.
    for d in payload.get("px_key_definitions", []):
        PxKeyDefinition.objects.update_or_create(
            id=d["id"],
            defaults={
                "name": d["name"],
                "key_type": d["key_type"],
                "consumable": d["consumable"],
                "fixed": d["fixed"],
                "unique": d["unique"],
                "project": project,
                "owner": user,
            },
        )

    lock_defs = payload.get("px_lock_definitions", [])
    for d in lock_defs:
        PxLockDefinition.objects.update_or_create(
            id=d["id"],
            defaults={
                "name": d["name"],
                "soft_gate": d["soft_gate"],
                "unlock_mode": d["unlock_mode"],
                "project": project,
                "owner": user,
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
