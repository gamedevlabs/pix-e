"""Load a frozen evaluation dataset JSON into an isolated project.

The dataset JSON is produced once by the ``export_eval_dataset`` management
command from a live pix:e project and then committed to the repo, so that
evaluation runs are reproducible and the ground truth stays valid.

Unlike the public ImportDataView (which regenerates UUIDs), this loader
**preserves the original UUIDs** of nodes, charts, etc. — keeping the dataset
stable across reloads. It also imports Pillars, which the standard export omits
but the Consistency agent needs for pillar-alignment checks.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import transaction

from pillars.models import Pillar
from projects.models import Project
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode

User = get_user_model()

EVAL_USER = "thesis_eval"


def load_dataset(path: str | Path, *, project_name: str | None = None) -> Project:
    """Load the dataset at ``path`` into a fresh, isolated eval project.

    Any previously loaded eval project with the same name (owned by the eval
    user) is deleted first, so reloading is idempotent.
    """
    data = json.loads(Path(path).read_text())

    user, _ = User.objects.get_or_create(
        username=EVAL_USER, defaults={"is_active": False}
    )

    proj_meta = data.get("project", {})
    name = project_name or proj_meta.get("name") or "EVAL Dataset"

    with transaction.atomic():
        # Wipe any prior load of this dataset (cascades to nodes/charts/...).
        Project.objects.filter(user=user, name=name).delete()

        project = Project.objects.create(
            user=user,
            name=name,
            description=proj_meta.get("description", ""),
            genres=proj_meta.get("genres", []),
            target_platforms=proj_meta.get("target_platforms", []),
            is_current=False,
        )

        _load_pillars(data, user, project)
        _load_definitions(data, user, project)
        _load_nodes(data, user, project)
        _load_components(data, user)
        _load_charts(data, user, project)
        _load_containers(data, user)
        _load_layouts(data)
        _load_edges(data, user)

    return project


def _load_pillars(data: Dict[str, Any], user, project: Project) -> None:
    # Pillar PKs are auto integers; we match pillars by name during evaluation,
    # so we deliberately do not force PKs (avoids collisions with other projects).
    for p in data.get("pillars", []):
        Pillar.objects.create(
            user=user,
            project=project,
            name=p.get("name", ""),
            description=p.get("description", ""),
        )


def _load_definitions(data: Dict[str, Any], user, project: Project) -> None:
    for d in data.get("pxcomponentdefinitions", []):
        PxComponentDefinition.objects.create(
            id=uuid.UUID(str(d["id"])),
            name=d.get("name", ""),
            type=d["type"],
            owner=user,
            project=project,
        )


def _load_nodes(data: Dict[str, Any], user, project: Project) -> None:
    for n in data.get("pxnodes", []):
        PxNode.objects.create(
            id=uuid.UUID(str(n["id"])),
            name=n.get("name", ""),
            description=n.get("description", ""),
            owner=user,
            project=project,
        )


def _load_components(data: Dict[str, Any], user) -> None:
    for c in data.get("pxcomponents", []):
        PxComponent.objects.create(
            id=uuid.UUID(str(c["id"])),
            node_id=uuid.UUID(str(c["node"])),
            definition_id=uuid.UUID(str(c["definition"])),
            value=c.get("value"),
            owner=user,
        )


def _load_charts(data: Dict[str, Any], user, project: Project) -> None:
    for ch in data.get("pxcharts", []):
        associated = ch.get("associatedNode")
        PxChart.objects.create(
            id=uuid.UUID(str(ch["id"])),
            name=ch.get("name", ""),
            description=ch.get("description", ""),
            associatedNode_id=uuid.UUID(str(associated)) if associated else None,
            owner=user,
            project=project,
        )


def _load_containers(data: Dict[str, Any], user) -> None:
    for c in data.get("pxchartcontainers", []):
        content = c.get("content")
        PxChartContainer.objects.create(
            id=uuid.UUID(str(c["id"])),
            name=c.get("name", ""),
            content_id=uuid.UUID(str(content)) if content else None,
            px_chart_id=uuid.UUID(str(c["px_chart"])),
            owner=user,
        )


def _load_layouts(data: Dict[str, Any]) -> None:
    for layout in data.get("pxchartcontainerlayouts", []):
        PxChartContainerLayout.objects.update_or_create(
            container_id=uuid.UUID(str(layout["container"])),
            defaults={
                "position_x": layout.get("position_x", 0),
                "position_y": layout.get("position_y", 0),
                "height": layout.get("height", 0),
                "width": layout.get("width", 0),
            },
        )


def _load_edges(data: Dict[str, Any], user) -> None:
    for e in data.get("pxchartedges", []):
        PxChartEdge.objects.create(
            id=uuid.UUID(str(e["id"])),
            px_chart_id=uuid.UUID(str(e["px_chart"])),
            source_id=uuid.UUID(str(e["source"])),
            sourceHandle=e.get("sourceHandle", ""),
            target_id=uuid.UUID(str(e["target"])),
            targetHandle=e.get("targetHandle", ""),
            owner=user,
        )
