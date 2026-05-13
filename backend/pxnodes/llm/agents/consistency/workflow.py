"""Orchestrates structural + semantic consistency checks for the pix:e schema."""

from typing import List, Optional

from game_concept.models import Project
from llm.providers.manager import ModelManager

from .schemas import ConsistencyFinding, ConsistencyReport, FindingSeverity
from .structural import StructuralChecker


class ConsistencyWorkflow:
    """Orchestrates structural + semantic consistency checks for a pix:e project.

    Note: unlike CoherenceWorkflow which evaluates a single node,
    consistency is inherently project-wide — relationships across
    entities are the unit of analysis.
    """

    def __init__(self, model_manager: Optional[ModelManager] = None) -> None:
        self._structural = StructuralChecker()
        self._model_manager = model_manager

    def check_project(self, project: Project) -> ConsistencyReport:
        findings: List[ConsistencyFinding] = []
        findings.extend(self._structural.check(project))
        if self._model_manager is not None:
            findings.extend(self._run_semantic_checks(project))
        return ConsistencyReport(findings=findings)

    def _run_semantic_checks(self, project: Project) -> List[ConsistencyFinding]:
        from .semantic.pillar_alignment import PillarAlignmentAgent

        if self._model_manager is None:
            return []

        findings: List[ConsistencyFinding] = []
        pillars = list(project.pillars.all())
        nodes = list(project.pxnodes.all())

        if not pillars or not nodes:
            return findings

        try:
            agent = PillarAlignmentAgent()
            data = {
                "pillars_section": self._format_pillars(pillars),
                "nodes_section": self._format_nodes(nodes),
            }
            context = {"model_manager": self._model_manager, "data": data}
            result = agent.execute(context)

            if result.success and result.data:
                for item in result.data.get("findings", []):
                    findings.append(
                        ConsistencyFinding(
                            severity=FindingSeverity.WARNING,
                            category="pillar_misalignment",
                            entity_id=item.get("node_id", ""),
                            message=(
                                f"[pillar {item.get('pillar_id', '')}] "
                                f"{item.get('explanation', '')} "
                                f"(confidence: {item.get('confidence', 0):.2f})"
                            ),
                        )
                    )
        except Exception:
            pass

        return findings

    def _format_pillars(self, pillars: list) -> str:
        lines = []
        for p in pillars:
            lines.append(
                f"- ID: {p.id}, Name: {p.name}\n  Description: {p.description}"
            )
        return "\n".join(lines)

    def _format_nodes(self, nodes: list) -> str:
        lines = []
        for n in nodes:
            lines.append(
                f"- ID: {n.id}, Name: {n.name}\n  Description: {n.description}"
            )
        return "\n".join(lines)
