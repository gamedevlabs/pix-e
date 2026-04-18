"""
Django management command to import PxNode, PxChart, and related data from JSON files.

Usage:
    python manage.py import_json_data path/to/file.json --user username
    python manage.py import_json_data path/to/file.json --user username --clear

This command imports data in the correct order to handle foreign key dependencies.
"""

import json
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from game_concept.models import Project
from game_concept.utils import get_current_project
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode

User = get_user_model()


class Command(BaseCommand):
    help = "Import PxNode, PxChart, and related data from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "json_file",
            type=str,
            help="Path to the JSON file to import",
        )
        parser.add_argument(
            "--user",
            type=str,
            required=True,
            help="Username of the owner for the imported data",
        )
        parser.add_argument(
            "--project-id",
            type=int,
            help="Project ID to attach imported data to (defaults to current)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data for the user before importing",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform a dry run without actually saving to the database",
        )

    def handle(self, *args, **options):
        json_file = options["json_file"]
        username = options["user"]
        clear_existing = options["clear"]
        dry_run = options["dry_run"]

        # Validate file exists
        file_path = Path(json_file)
        if not file_path.exists():
            raise CommandError(f"File '{json_file}' does not exist")

        # Get user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' does not exist")

        project_id = options.get("project_id")
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=user)
            except Project.DoesNotExist:
                raise CommandError(
                    f"Project '{project_id}' not found for user '{username}'"
                )
        else:
            project = get_current_project(user)

        # Load JSON data
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON file: {e}")

        self.stdout.write(self.style.SUCCESS(f"Loaded data from {json_file}"))

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be saved")
            )

        # Import data in a transaction
        try:
            with transaction.atomic():
                if clear_existing:
                    self._clear_existing_data(user, project, dry_run)

                stats = self._import_data(data, user, project, dry_run)

                if dry_run:
                    # Rollback the transaction
                    raise Exception("Dry run - rolling back")

        except Exception as e:
            if dry_run and str(e) == "Dry run - rolling back":
                self.stdout.write(
                    self.style.SUCCESS("\nDry run completed successfully!")
                )
                self._print_stats(stats)
            else:
                raise CommandError(f"Error during import: {e}")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ Data imported successfully!"))
            self._print_stats(stats)

    def _clear_existing_data(self, user, project, dry_run):
        """Clear existing data for the user/project"""
        self.stdout.write(self.style.WARNING("\nClearing existing data..."))

        # Models with owner field
        models_with_owner = [
            (PxChartEdge, "chart edges"),
            (PxChartContainer, "chart containers"),
            (PxChart, "charts"),
            (PxComponent, "components"),
            (PxComponentDefinition, "component definitions"),
            (PxNode, "nodes"),
        ]

        node_filters = {"owner": user}
        chart_filters = {"owner": user}
        definition_filters = {"owner": user}
        if project:
            node_filters["project"] = project
            chart_filters["project"] = project
            definition_filters["project"] = project
        else:
            node_filters["project__isnull"] = True
            chart_filters["project__isnull"] = True
            definition_filters["project__isnull"] = True

        charts = PxChart.objects.filter(**chart_filters)
        # Clear chart edges first
        for model, name in [models_with_owner[0]]:
            count = model.objects.filter(owner=user, px_chart__in=charts).count()
            if count > 0:
                self.stdout.write(f"  Deleting {count} {name}...")
                if not dry_run:
                    model.objects.filter(owner=user, px_chart__in=charts).delete()

        # Clear chart container layouts (through their containers)
        containers = PxChartContainer.objects.filter(owner=user, px_chart__in=charts)
        layout_count = PxChartContainerLayout.objects.filter(
            container__in=containers
        ).count()
        if layout_count > 0:
            self.stdout.write(f"  Deleting {layout_count} chart container layouts...")
            if not dry_run:
                PxChartContainerLayout.objects.filter(container__in=containers).delete()

        # Clear remaining models with owner
        for model, name in models_with_owner[1:]:
            if model is PxChart:
                count = model.objects.filter(**chart_filters).count()
                if count > 0:
                    self.stdout.write(f"  Deleting {count} {name}...")
                    if not dry_run:
                        model.objects.filter(**chart_filters).delete()
                continue
            if model is PxComponentDefinition:
                count = model.objects.filter(**definition_filters).count()
                if count > 0:
                    self.stdout.write(f"  Deleting {count} {name}...")
                    if not dry_run:
                        model.objects.filter(**definition_filters).delete()
                continue
            if model is PxComponent:
                node_queryset = PxNode.objects.filter(**node_filters)
                count = model.objects.filter(
                    owner=user,
                    node__in=node_queryset,
                ).count()
                if count > 0:
                    self.stdout.write(f"  Deleting {count} {name}...")
                    if not dry_run:
                        model.objects.filter(
                            owner=user,
                            node__in=node_queryset,
                        ).delete()
                continue
            count = model.objects.filter(**node_filters).count()
            if count > 0:
                self.stdout.write(f"  Deleting {count} {name}...")
                if not dry_run:
                    model.objects.filter(**node_filters).delete()

    def _import_data(self, data, user, project, dry_run):
        """Import all data from the JSON structure"""
        stats = {
            "nodes": 0,
            "component_definitions": 0,
            "components": 0,
            "charts": 0,
            "containers": 0,
            "layouts": 0,
            "edges": 0,
        }

        # Import in dependency order
        self.stdout.write("\nImporting data...")

        # 1. Import PxNodes
        if "pxnodes" in data:
            stats["nodes"] = self._import_nodes(data["pxnodes"], user, project, dry_run)

        # 2. Import PxComponentDefinitions
        if "pxcomponentdefinitions" in data:
            stats["component_definitions"] = self._import_component_definitions(
                data["pxcomponentdefinitions"], user, project, dry_run
            )

        # 3. Import PxCharts
        if "pxcharts" in data:
            stats["charts"] = self._import_charts(
                data["pxcharts"], user, project, dry_run
            )

        # 4. Import PxComponents
        if "pxcomponents" in data:
            stats["components"] = self._import_components(
                data["pxcomponents"], user, dry_run
            )

        # 5. Import PxChartContainers
        if "pxchartcontainers" in data:
            stats["containers"] = self._import_containers(
                data["pxchartcontainers"], user, dry_run
            )

        # 6. Import PxChartContainerLayouts
        if "pxchartcontainerlayouts" in data:
            stats["layouts"] = self._import_layouts(
                data["pxchartcontainerlayouts"], user, dry_run
            )

        # 7. Import PxChartEdges
        if "pxchartedges" in data:
            stats["edges"] = self._import_edges(data["pxchartedges"], user, dry_run)

        return stats

    def _import_nodes(self, nodes_data, user, project, dry_run):
        """Import PxNode objects"""
        self.stdout.write("  Importing nodes...")
        count = 0

        for node_data in nodes_data:
            node_id = uuid.UUID(node_data["id"])
            node = PxNode(
                id=node_id,
                name=node_data["name"],
                description=node_data.get("description", ""),
                owner=user,
                project=project,
            )
            if not dry_run:
                node.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} nodes")
        return count

    def _import_component_definitions(self, definitions_data, user, project, dry_run):
        """Import PxComponentDefinition objects"""
        self.stdout.write("  Importing component definitions...")
        count = 0

        for def_data in definitions_data:
            def_id = uuid.UUID(def_data["id"])
            definition = PxComponentDefinition(
                id=def_id,
                name=def_data["name"],
                type=def_data["type"],
                owner=user,
                project=project,
            )
            if not dry_run:
                definition.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} component definitions")
        return count

    def _import_charts(self, charts_data, user, project, dry_run):
        """Import PxChart objects"""
        self.stdout.write("  Importing charts...")
        count = 0

        for chart_data in charts_data:
            chart_id = uuid.UUID(chart_data["id"])
            associated_node = None
            if chart_data.get("associatedNode"):
                node_id = uuid.UUID(chart_data["associatedNode"])
                if not dry_run:
                    associated_node = PxNode.objects.get(id=node_id, owner=user)
                else:
                    # In dry run, create a temporary reference
                    associated_node = PxNode(id=node_id, owner=user)

            chart = PxChart(
                id=chart_id,
                name=chart_data["name"],
                description=chart_data.get("description", ""),
                associatedNode=associated_node,
                owner=user,
                project=project,
            )
            if not dry_run:
                chart.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} charts")
        return count

    def _import_components(self, components_data, user, dry_run):
        """Import PxComponent objects"""
        self.stdout.write("  Importing components...")
        count = 0

        for comp_data in components_data:
            comp_id = uuid.UUID(comp_data["id"])
            node_id = uuid.UUID(comp_data["node"])
            def_id = uuid.UUID(comp_data["definition"])

            if not dry_run:
                node = PxNode.objects.get(id=node_id, owner=user)
                definition = PxComponentDefinition.objects.get(id=def_id, owner=user)
            else:
                node = PxNode(id=node_id, owner=user)
                definition = PxComponentDefinition(id=def_id, owner=user)

            component = PxComponent(
                id=comp_id,
                node=node,
                definition=definition,
                value=comp_data["value"],
                owner=user,
            )
            if not dry_run:
                component.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} components")
        return count

    def _import_containers(self, containers_data, user, dry_run):
        """Import PxChartContainer objects"""
        self.stdout.write("  Importing chart containers...")
        count = 0

        for container_data in containers_data:
            container_id = uuid.UUID(container_data["id"])
            chart_id = uuid.UUID(container_data["px_chart"])

            if not dry_run:
                chart = PxChart.objects.get(id=chart_id, owner=user)
                content = None
                if container_data.get("content"):
                    content_id = uuid.UUID(container_data["content"])
                    content = PxNode.objects.get(id=content_id, owner=user)
            else:
                chart = PxChart(id=chart_id, owner=user)
                content = None
                if container_data.get("content"):
                    content_id = uuid.UUID(container_data["content"])
                    content = PxNode(id=content_id, owner=user)

            container = PxChartContainer(
                id=container_id,
                px_chart=chart,
                name=container_data["name"],
                content=content,
                owner=user,
            )
            if not dry_run:
                container.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} chart containers")
        return count

    def _import_layouts(self, layouts_data, user, dry_run):
        """Import PxChartContainerLayout objects"""
        self.stdout.write("  Importing chart container layouts...")
        count = 0

        for layout_data in layouts_data:
            container_id = uuid.UUID(layout_data["container"])

            if not dry_run:
                container = PxChartContainer.objects.get(id=container_id, owner=user)
                # Use update_or_create since it's a OneToOneField
                layout, created = PxChartContainerLayout.objects.update_or_create(
                    container=container,
                    defaults={
                        "position_x": layout_data.get("position_x", 0),
                        "position_y": layout_data.get("position_y", 0),
                        "height": layout_data.get("height", 0),
                        "width": layout_data.get("width", 0),
                    },
                )
            count += 1

        self.stdout.write(f"    ✓ Imported {count} chart container layouts")
        return count

    def _import_edges(self, edges_data, user, dry_run):
        """Import PxChartEdge objects"""
        self.stdout.write("  Importing chart edges...")
        count = 0

        for edge_data in edges_data:
            edge_id = uuid.UUID(edge_data["id"])
            chart_id = uuid.UUID(edge_data["px_chart"])
            source_id = uuid.UUID(edge_data["source"])
            target_id = uuid.UUID(edge_data["target"])

            if not dry_run:
                chart = PxChart.objects.get(id=chart_id, owner=user)
                source = PxChartContainer.objects.get(id=source_id, owner=user)
                target = PxChartContainer.objects.get(id=target_id, owner=user)
            else:
                chart = PxChart(id=chart_id, owner=user)
                source = PxChartContainer(id=source_id, owner=user)
                target = PxChartContainer(id=target_id, owner=user)

            edge = PxChartEdge(
                id=edge_id,
                px_chart=chart,
                source=source,
                sourceHandle=edge_data.get("sourceHandle", ""),
                target=target,
                targetHandle=edge_data.get("targetHandle", ""),
                owner=user,
            )
            if not dry_run:
                edge.save()
            count += 1

        self.stdout.write(f"    ✓ Imported {count} chart edges")
        return count

    def _print_stats(self, stats):
        """Print import statistics"""
        self.stdout.write("\nImport Summary:")
        self.stdout.write(f"  • Nodes: {stats['nodes']}")
        self.stdout.write(
            f"  • Component Definitions: {stats['component_definitions']}"
        )
        self.stdout.write(f"  • Components: {stats['components']}")
        self.stdout.write(f"  • Charts: {stats['charts']}")
        self.stdout.write(f"  • Chart Containers: {stats['containers']}")
        self.stdout.write(f"  • Chart Container Layouts: {stats['layouts']}")
        self.stdout.write(f"  • Chart Edges: {stats['edges']}")
        self.stdout.write(f"\n  Total: {sum(stats.values())} objects")
