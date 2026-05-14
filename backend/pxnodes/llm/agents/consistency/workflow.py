import logging
from typing import List, Optional

from game_concept.models import Project
from llm.providers.manager import ModelManager

from .schemas import ConsistencyFinding, ConsistencyReport, FindingSeverity
from .structural import StructuralChecker

logger = logging.getLogger(__name__)


class ConsistencyWorkflow:
    """Orchestrates structural + semantic consistency checks for a pix:e project.

    Note: unlike CoherenceWorkflow which evaluates a single node,
    consistency is inherently project-wide — relationships across
    entities are the unit of analysis.
    """

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        min_confidence: float = 0.0,
    ) -> None:
        self._structural = StructuralChecker()
        self._model_manager = model_manager
        self._min_confidence = min_confidence

    def check_project(self, project: Project) -> ConsistencyReport:
        findings: List[ConsistencyFinding] = []
        findings.extend(self._structural.check(project))
        if self._model_manager is not None:
            findings.extend(self._run_semantic_checks(project))
        return ConsistencyReport(findings=findings)

    def _run_semantic_checks(self, project: Project) -> List[ConsistencyFinding]:
        from .semantic.node_coherence import NodeCoherenceAgent
        from .semantic.pillar_alignment import PillarAlignmentAgent
        from .semantic.terminology_consistency import TerminologyConsistencyAgent

        if self._model_manager is None:
            return []

        findings: List[ConsistencyFinding] = []
        pillars = list(project.pillars.all())
        nodes = list(project.pxnodes.all())

        if pillars and nodes:
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
                        if item.get("confidence", 1.0) < self._min_confidence:
                            continue
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
            except Exception as e:
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    agent.__class__.__name__,
                    e,
                )

        if len(nodes) >= 2:
            try:
                agent = NodeCoherenceAgent()
                data = {
                    "nodes": [
                        {
                            "id": str(n.id),
                            "name": n.name,
                            "description": n.description,
                        }
                        for n in nodes
                    ],
                }
                context = {"model_manager": self._model_manager, "data": data}
                result = agent.execute(context)
                if result.success and result.data:
                    for item in result.data.get("contradictions", []):
                        if item.get("confidence", 1.0) < self._min_confidence:
                            continue
                        findings.append(
                            ConsistencyFinding(
                                severity=FindingSeverity.WARNING,
                                category="node_contradiction",
                                entity_id=item.get("node_a_id", ""),
                                message=(
                                    f"[vs {item.get('node_b_name', '')}] "
                                    f"{item.get('message', '')}"
                                ),
                            )
                        )
            except Exception as e:
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    agent.__class__.__name__,
                    e,
                )

        if len(nodes) >= 2:
            try:
                agent = TerminologyConsistencyAgent()
                data = {
                    "nodes": [
                        {
                            "id": str(n.id),
                            "name": n.name,
                            "description": n.description,
                        }
                        for n in nodes
                    ],
                }
                context = {"model_manager": self._model_manager, "data": data}
                result = agent.execute(context)
                if result.success and result.data:
                    for item in result.data.get("conflicts", []):
                        if item.get("confidence", 1.0) < self._min_confidence:
                            continue
                        findings.append(
                            ConsistencyFinding(
                                severity=FindingSeverity.INFO,
                                category="terminology_inconsistency",
                                entity_id=item.get("node_a_id", ""),
                                message=(
                                    f"['{item.get('term_a', '')}' vs "
                                    f"'{item.get('term_b', '')}' in "
                                    f"{item.get('node_b_name', '')}] "
                                    f"{item.get('message', '')}"
                                ),
                            )
                        )
            except Exception as e:
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    agent.__class__.__name__,
                    e,
                )

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
