"""
Service helpers for game_concept operations.
"""

import uuid

from django.contrib.auth.models import User

from pillars.models import Pillar
from pxcharts.models import (
    PxChart,
    PxChartContainer,
    PxChartContainerLayout,
    PxChartEdge,
)
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode

from .models import GameConcept, Project


def clone_project(
    *,
    source_project: Project,
    user: User,
    name: str,
    include_concept: bool,
    include_pillars: bool,
    include_charts: bool,
    include_nodes: bool,
) -> Project:
    new_project = Project.objects.create(
        user=user,
        name=name,
        description=source_project.description,
        is_current=False,
    )

    def_map: dict[str, PxComponentDefinition] = {}
    node_map: dict[str, PxNode] = {}

    if include_concept:
        concepts = GameConcept.objects.filter(project=source_project).order_by(
            "created_at"
        )
        for concept in concepts:
            GameConcept.objects.create(
                user=user,
                project=new_project,
                content=concept.content,
                is_current=concept.is_current,
                last_sparc_evaluation=concept.last_sparc_evaluation,
            )

    if include_pillars:
        pillars = Pillar.objects.filter(project=source_project)
        for pillar in pillars:
            Pillar.objects.create(
                user=user,
                project=new_project,
                name=pillar.name,
                description=pillar.description,
            )

    if include_nodes:
        _clone_nodes(
            source_project=source_project,
            new_project=new_project,
            user=user,
            def_map=def_map,
            node_map=node_map,
        )

    if include_charts:
        _clone_charts(
            source_project=source_project,
            new_project=new_project,
            user=user,
            include_nodes=include_nodes,
            node_map=node_map,
        )

    return new_project


def _clone_nodes(
    *,
    source_project: Project,
    new_project: Project,
    user: User,
    def_map: dict[str, PxComponentDefinition],
    node_map: dict[str, PxNode],
) -> None:
    definitions = PxComponentDefinition.objects.filter(project=source_project)
    for definition in definitions:
        new_def = PxComponentDefinition.objects.create(
            id=uuid.uuid4(),
            name=definition.name,
            type=definition.type,
            owner=user,
            project=new_project,
        )
        def_map[str(definition.id)] = new_def

    nodes = PxNode.objects.filter(project=source_project)
    for node in nodes:
        new_node = PxNode.objects.create(
            id=uuid.uuid4(),
            name=node.name,
            description=node.description,
            owner=user,
            project=new_project,
        )
        node_map[str(node.id)] = new_node

        components = node.components.all()
        for component in components:
            comp_def = def_map.get(str(component.definition_id))
            if not comp_def:
                comp_def = PxComponentDefinition.objects.create(
                    id=uuid.uuid4(),
                    name=component.definition.name,
                    type=component.definition.type,
                    owner=user,
                    project=new_project,
                )
                def_map[str(component.definition_id)] = comp_def
            PxComponent.objects.create(
                id=uuid.uuid4(),
                node=new_node,
                definition=comp_def,
                value=component.value,
                owner=user,
            )


def _clone_charts(
    *,
    source_project: Project,
    new_project: Project,
    user: User,
    include_nodes: bool,
    node_map: dict[str, PxNode],
) -> None:
    charts = PxChart.objects.filter(project=source_project)
    for chart in charts:
        new_associated_node = None
        if include_nodes and chart.associatedNode:
            new_associated_node = node_map.get(str(chart.associatedNode_id))

        new_chart = PxChart.objects.create(
            id=uuid.uuid4(),
            name=chart.name,
            description=chart.description,
            project=new_project,
            associatedNode=new_associated_node,
            owner=user,
        )

        container_map: dict[str, PxChartContainer] = {}
        for container in chart.containers.all():
            new_content = None
            if include_nodes and container.content_id:
                new_content = node_map.get(str(container.content_id))
            new_container = PxChartContainer.objects.create(
                id=uuid.uuid4(),
                px_chart=new_chart,
                name=container.name,
                content=new_content,
                owner=user,
            )
            container_map[str(container.id)] = new_container
            _clone_container_layout(container, new_container)

        for edge in chart.edges.all():
            new_source = container_map.get(str(edge.source_id))
            new_target = container_map.get(str(edge.target_id))
            PxChartEdge.objects.create(
                id=uuid.uuid4(),
                px_chart=new_chart,
                source=new_source,
                sourceHandle=edge.sourceHandle,
                target=new_target,
                targetHandle=edge.targetHandle,
                owner=user,
            )


def _clone_container_layout(
    container: PxChartContainer, new_container: PxChartContainer
) -> None:
    if not hasattr(container, "layout") or not container.layout:
        return

    layout = getattr(new_container, "layout", None)
    if layout:
        layout.position_x = container.layout.position_x
        layout.position_y = container.layout.position_y
        layout.height = container.layout.height
        layout.width = container.layout.width
        layout.save(update_fields=["position_x", "position_y", "height", "width"])
    else:
        PxChartContainerLayout.objects.create(
            container=new_container,
            position_x=container.layout.position_x,
            position_y=container.layout.position_y,
            height=container.layout.height,
            width=container.layout.width,
        )
