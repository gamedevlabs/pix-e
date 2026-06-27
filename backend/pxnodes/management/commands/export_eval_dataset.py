"""Export a live pix:e project to a frozen evaluation dataset JSON.

Run once to snapshot the Anno 1404 (or any) project, then commit the resulting
file so evaluation runs are reproducible. Unlike the public data export, this
includes Pillars and project metadata, and preserves all UUIDs.

Usage:
    python manage.py export_eval_dataset --project-id 42 \
        --out pxnodes/llm/eval/dataset/anno1404.json
"""

import json

from django.core.management.base import BaseCommand, CommandError

from pillars.models import Pillar
from projects.models import Project
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode


class Command(BaseCommand):
    help = "Export a project (incl. pillars) to a frozen evaluation dataset JSON."

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=int, required=True)
        parser.add_argument("--out", type=str, required=True, help="Output JSON path")

    def handle(self, *args, **options):
        try:
            project = Project.objects.get(id=options["project_id"])
        except Project.DoesNotExist:
            raise CommandError(f"Project {options['project_id']} not found")

        nodes = PxNode.objects.filter(project=project)
        definitions = PxComponentDefinition.objects.filter(project=project)
        components = PxComponent.objects.filter(node__project=project)
        charts = PxChart.objects.filter(project=project)
        containers = PxChartContainer.objects.filter(px_chart__project=project)
        layouts = PxChartContainerLayout.objects.filter(
            container__px_chart__project=project
        )
        edges = PxChartEdge.objects.filter(px_chart__project=project)
        pillars = Pillar.objects.filter(project=project)

        data = {
            "project": {
                "name": project.name,
                "description": project.description,
                "genres": project.genres,
                "target_platforms": project.target_platforms,
            },
            "pillars": [
                {"name": p.name, "description": p.description} for p in pillars
            ],
            "pxcomponentdefinitions": [
                {"id": str(d.id), "name": d.name, "type": d.type} for d in definitions
            ],
            "pxnodes": [
                {"id": str(n.id), "name": n.name, "description": n.description}
                for n in nodes
            ],
            "pxcomponents": [
                {
                    "id": str(c.id),
                    "node": str(c.node_id),
                    "definition": str(c.definition_id),
                    "value": c.value,
                }
                for c in components
            ],
            "pxcharts": [
                {
                    "id": str(ch.id),
                    "name": ch.name,
                    "description": ch.description,
                    "associatedNode": (
                        str(ch.associatedNode_id) if ch.associatedNode_id else None
                    ),
                }
                for ch in charts
            ],
            "pxchartcontainers": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "content": str(c.content_id) if c.content_id else None,
                    "px_chart": str(c.px_chart_id),
                }
                for c in containers
            ],
            "pxchartcontainerlayouts": [
                {
                    "container": str(layout.container_id),
                    "position_x": layout.position_x,
                    "position_y": layout.position_y,
                    "height": layout.height,
                    "width": layout.width,
                }
                for layout in layouts
            ],
            "pxchartedges": [
                {
                    "id": str(e.id),
                    "px_chart": str(e.px_chart_id),
                    "source": str(e.source_id),
                    "sourceHandle": e.sourceHandle,
                    "target": str(e.target_id),
                    "targetHandle": e.targetHandle,
                }
                for e in edges
            ],
        }

        with open(options["out"], "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported project '{project.name}': "
                f"{len(data['pxnodes'])} nodes, {len(data['pillars'])} pillars, "
                f"{len(data['pxchartedges'])} edges → {options['out']}"
            )
        )
