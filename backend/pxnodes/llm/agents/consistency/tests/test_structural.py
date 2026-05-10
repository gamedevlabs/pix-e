"""Tests for Layer 1 structural consistency checks (StructuralChecker)."""

import uuid
from unittest.mock import Mock, patch

import pytest

from pxcharts.models import PxChart, PxChartContainer, PxChartEdge
from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.structural import StructuralChecker
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode

# Helpers

def make_node(project, name="Node"):
    return PxNode.objects.create(
        id=uuid.uuid4(), name=name, description="", project=project
    )


def make_definition(project, name="Def"):
    return PxComponentDefinition.objects.create(
        id=uuid.uuid4(), name=name, type="string", project=project
    )


def make_component(node, definition):
    return PxComponent.objects.create(
        id=uuid.uuid4(), node=node, definition=definition, value="test"
    )


def make_chart(project, name="Chart"):
    return PxChart.objects.create(
        id=uuid.uuid4(), name=name, description="", project=project
    )


def make_container(chart, content=None, name="Container"):
    return PxChartContainer.objects.create(
        id=uuid.uuid4(), px_chart=chart, name=name, content=content
    )


def make_edge(chart, source, target, source_handle="a", target_handle="b"):
    return PxChartEdge.objects.create(
        id=uuid.uuid4(),
        px_chart=chart,
        source=source,
        sourceHandle=source_handle,
        target=target,
        targetHandle=target_handle,
    )


# Regel 1: PxComponent.definition gehört zu einem anderen Projekt

@pytest.mark.django_db
class TestCheckComponentProjectMatch:
    def test_cross_project_definition_raises_finding(self, project_a, project_b):
        node = make_node(project_a)
        definition = make_definition(project_b)
        make_component(node, definition)

        findings = StructuralChecker()._check_component_project_match(project_a)

        assert len(findings) == 1
        assert findings[0].category == "cross_project_definition"
        assert findings[0].severity == FindingSeverity.ERROR

    def test_same_project_definition_no_finding(self, project_a):
        node = make_node(project_a)
        definition = make_definition(project_a)
        make_component(node, definition)

        findings = StructuralChecker()._check_component_project_match(project_a)

        assert findings == []

    def test_definition_none_is_skipped(self):
        """Null guard: a component whose definition is None produces no finding."""
        mock_component = Mock()
        mock_component.definition = None

        with patch(
            "pxnodes.llm.agents.consistency.structural.PxComponent.objects"
        ) as mock_objects:
            mock_objects.filter.return_value.select_related.return_value = [
                mock_component
            ]
            findings = StructuralChecker()._check_component_project_match(Mock())

        assert findings == []



# Regel 2: PxChartContainer.content gehört zu einem anderen Projekt als sein PxChart


@pytest.mark.django_db
class TestCheckChartContainerProjectMatch:
    def test_cross_project_content_raises_finding(self, project_a, project_b):
        chart = make_chart(project_a)
        node = make_node(project_b, name="ForeignNode")
        make_container(chart, content=node)

        findings = StructuralChecker()._check_chart_container_project_match(project_a)

        assert len(findings) == 1
        assert findings[0].category == "cross_project_chart_container"
        assert findings[0].severity == FindingSeverity.ERROR

    def test_same_project_content_no_finding(self, project_a):
        chart = make_chart(project_a)
        node = make_node(project_a)
        make_container(chart, content=node)

        findings = StructuralChecker()._check_chart_container_project_match(project_a)

        assert findings == []

    def test_content_none_no_finding(self, project_a):
        """Null guard: container without content (empty slot) produces no finding."""
        chart = make_chart(project_a)
        make_container(chart, content=None)

        findings = StructuralChecker()._check_chart_container_project_match(project_a)

        assert findings == []


# Regel 3: PxChartEdge verbindet Container aus verschiedenen Charts


@pytest.mark.django_db
class TestCheckEdgeWithinSameChart:
    def test_edge_spans_charts_raises_finding(self, project_a):
        chart_a = make_chart(project_a, name="ChartA")
        chart_b = make_chart(project_a, name="ChartB")
        container_a = make_container(chart_a, name="ContainerA")
        container_b = make_container(chart_b, name="ContainerB")
        make_edge(chart_a, source=container_a, target=container_b)

        findings = StructuralChecker()._check_edge_within_same_chart(project_a)

        assert len(findings) == 1
        assert findings[0].category == "edge_spans_multiple_charts"
        assert findings[0].severity == FindingSeverity.ERROR

    def test_edge_within_same_chart_no_finding(self, project_a):
        chart = make_chart(project_a)
        container_a = make_container(chart, name="ContainerA")
        container_b = make_container(chart, name="ContainerB")
        make_edge(chart, source=container_a, target=container_b)

        findings = StructuralChecker()._check_edge_within_same_chart(project_a)

        assert findings == []

    def test_source_or_target_none_skipped(self, project_a):
        """Null guard: edge with source=None (dangling after container deletion) produces no finding."""
        chart = make_chart(project_a)
        container = make_container(chart)
        make_edge(chart, source=None, target=container)

        findings = StructuralChecker()._check_edge_within_same_chart(project_a)

        assert findings == []
