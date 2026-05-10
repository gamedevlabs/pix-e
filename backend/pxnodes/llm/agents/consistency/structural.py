"""Layer 1: deterministic schema/reference consistency checks."""

from typing import List

from django.db.models import Count
from game_concept.models import Project
from pxcharts.models import PxChartContainer, PxChartEdge
from pxnodes.models import PxComponent, PxNode

from .schemas import ConsistencyFinding, FindingSeverity


class StructuralChecker:
    """Layer 1: deterministic schema/reference consistency checks."""

    def check(self, project: Project) -> List[ConsistencyFinding]:
        findings: List[ConsistencyFinding] = []
        findings.extend(self._check_component_project_match(project))
        findings.extend(self._check_chart_container_project_match(project))
        findings.extend(self._check_edge_within_same_chart(project))
        findings.extend(self._check_component_value_type_match(project))
        findings.extend(self._check_duplicate_node_names(project))
        return findings

    def _check_component_project_match(
        self, project: Project
    ) -> List[ConsistencyFinding]:
        """Check each PxComponent's definition belongs to the node's project."""
        components = (
            PxComponent.objects.filter(node__project=project)
            .select_related("node", "definition", "definition__project")
        )
        findings = []
        for c in components:
            if c.definition is None:
                continue  # other rule handles missing definition
            if c.definition.project_id != c.node.project_id:
                msg = (
                    f"PxComponent {c.id} on node '{c.node.name}' uses "
                    f"definition '{c.definition.name}' from a different project."
                )
                findings.append(
                    ConsistencyFinding(
                        severity=FindingSeverity.ERROR,
                        category="cross_project_definition",
                        entity_id=str(c.id),
                        message=msg,
                    )
                )
        return findings

    def _check_chart_container_project_match(
        self, project: Project
    ) -> List[ConsistencyFinding]:
        """Check each PxChartContainer's content (PxNode) belongs to the same project as its PxChart."""
        containers = (
            PxChartContainer.objects.filter(px_chart__project=project)
            .select_related("px_chart", "content", "content__project")
        )
        findings = []
        for container in containers:
            if container.content is None:
                continue
            if container.content.project_id != container.px_chart.project_id:
                msg = (
                    f"PxChartContainer '{container.name}' (id={container.id}) "
                    f"on chart '{container.px_chart.name}' contains node "
                    f"'{container.content.name}' from a different project."
                )
                findings.append(
                    ConsistencyFinding(
                        severity=FindingSeverity.ERROR,
                        category="cross_project_chart_container",
                        entity_id=str(container.id),
                        message=msg,
                    )
                )
        return findings

    def _check_component_value_type_match(
        self, project: Project
    ) -> List[ConsistencyFinding]:
        """Check each PxComponent's value type matches its definition's declared type."""
        components = (
            PxComponent.objects.filter(node__project=project)
            .select_related("node", "definition")
        )
        findings = []
        for c in components:
            if c.definition is None:
                continue
            if c.value is None:
                continue
            value = c.value
            expected = c.definition.type
            if expected == "number":
                # bool is a subclass of int in Python, so exclude it explicitly
                ok = isinstance(value, (int, float)) and not isinstance(value, bool)
            elif expected == "string":
                ok = isinstance(value, str)
            elif expected == "bool":
                ok = isinstance(value, bool)
            else:
                # unknown type, ignore
                continue
            if not ok:
                msg = (
                    f"PxComponent {c.id} expected '{expected}' but value is of "
                    f"type '{type(value).__name__}'."
                )
                findings.append(
                    ConsistencyFinding(
                        severity=FindingSeverity.ERROR,
                        category="value_type_mismatch",
                        entity_id=str(c.id),
                        message=msg,
                    )
                )
        return findings

    def _check_edge_within_same_chart(
        self, project: Project
    ) -> List[ConsistencyFinding]:
        """Check each PxChartEdge's source and target reside in the same chart."""
        edges = (
            PxChartEdge.objects.filter(px_chart__project=project)
            .select_related("source", "target", "source__px_chart", "target__px_chart")
        )
        findings = []
        for edge in edges:
            if edge.source is None or edge.target is None:
                continue
            if edge.source.px_chart_id != edge.target.px_chart_id:
                msg = (
                    f"PxChartEdge {edge.id} connects container '{edge.source.name}' "
                    f"(chart '{edge.source.px_chart.name}') to container "
                    f"'{edge.target.name}' (chart '{edge.target.px_chart.name}') "
                    f"across different charts."
                )
                findings.append(
                    ConsistencyFinding(
                        severity=FindingSeverity.ERROR,
                        category="edge_spans_multiple_charts",
                        entity_id=str(edge.id),
                        message=msg,
                    )
                )
        return findings

    def _check_duplicate_node_names(
        self, project: Project
    ) -> List[ConsistencyFinding]:
        """Warn when multiple PxNodes share the same name within a project."""
        duplicates = (
            PxNode.objects.filter(project=project)
            .values("name")
            .annotate(count=Count("id"))
            .filter(count__gt=1)
        )
        findings = []
        for dup in duplicates:
            name = dup["name"]
            ids = list(
                PxNode.objects.filter(project=project, name=name)
                .values_list("id", flat=True)
            )
            msg = (
                f"Multiple PxNodes share the name '{name}' in this project "
                f"({len(ids)} nodes: {', '.join(str(i) for i in ids)})."
            )
            findings.append(
                ConsistencyFinding(
                    severity=FindingSeverity.WARNING,
                    category="duplicate_node_name",
                    entity_id=str(ids[0]),
                    message=msg,
                )
            )
        return findings
