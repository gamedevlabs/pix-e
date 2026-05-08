"""Layer 1: deterministic schema/reference consistency checks."""

from typing import List

from game_concept.models import Project
from pxnodes.models import PxComponent

from .schemas import ConsistencyFinding, FindingSeverity


class StructuralChecker:
    """Layer 1: deterministic schema/reference consistency checks."""

    def check(self, project: Project) -> List[ConsistencyFinding]:
        findings: List[ConsistencyFinding] = []
        findings.extend(self._check_component_project_match(project))
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
