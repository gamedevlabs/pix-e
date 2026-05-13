"""Orchestrates structural + semantic consistency checks for the pix:e schema."""

from game_concept.models import Project

from .schemas import ConsistencyReport
from .structural import StructuralChecker


class ConsistencyWorkflow:
    """Orchestrates structural + semantic consistency checks for a pix:e project.

    Note: unlike CoherenceWorkflow which evaluates a single node,
    consistency is inherently project-wide — relationships across
    entities are the unit of analysis.
    """

    def __init__(self) -> None:
        self._structural = StructuralChecker()
        # self._semantic = SemanticConsistencyAgent()  # Layer 2, later

    def check_project(self, project: Project) -> ConsistencyReport:
        findings = []
        findings.extend(self._structural.check(project))
        # findings.extend(self._semantic.check(project))  # later
        return ConsistencyReport(findings=findings)
