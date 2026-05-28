import logging
from typing import Any, List, Optional

from game_concept.models import Project
from llm.exceptions import RateLimitError
from llm.providers.manager import ModelManager

from .schemas import ConsistencyFinding, ConsistencyMeta, ConsistencyReport, FindingSeverity
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
        run_structural: bool = True,
        model_id: Optional[str] = None,
    ) -> None:
        self._structural = StructuralChecker()
        self._model_manager = model_manager
        self._min_confidence = min_confidence
        self._run_structural = run_structural
        self._model_id = model_id

    def check_project(self, project: Project) -> ConsistencyReport:
        findings: List[ConsistencyFinding] = []
        agents_run: List[str] = []
        agents_skipped: dict = {}

        if self._run_structural:
            findings.extend(self._structural.check(project))
            agents_run.append("structural")
        else:
            agents_skipped["structural"] = "layers=semantic"

        if self._model_manager is not None:
            semantic_findings, semantic_run, semantic_skipped = (
                self._run_semantic_checks(project)
            )
            findings.extend(semantic_findings)
            agents_run.extend(semantic_run)
            agents_skipped.update(semantic_skipped)
        else:
            agents_skipped["pillar_alignment"] = "no model_manager (layers=structural)"
            agents_skipped["node_coherence"] = "no model_manager (layers=structural)"
            agents_skipped["terminology_consistency"] = (
                "no model_manager (layers=structural)"
            )

        nodes = list(project.pxnodes.all())
        pillars = list(project.pillars.all())
        meta = ConsistencyMeta(
            nodes_checked=len(nodes),
            pillars_checked=len(pillars),
            agents_run=agents_run,
            agents_skipped=agents_skipped,
        )
        return ConsistencyReport(findings=findings, meta=meta)

    def _run_semantic_checks(
        self, project: Project
    ) -> tuple[List[ConsistencyFinding], List[str], dict]:
        from .semantic.node_coherence import NodeCoherenceAgent
        from .semantic.pillar_alignment import PillarAlignmentAgent
        from .semantic.terminology_consistency import TerminologyConsistencyAgent

        if self._model_manager is None:
            return [], [], {}

        findings: List[ConsistencyFinding] = []
        agents_run: List[str] = []
        agents_skipped: dict = {}
        pillars = list(project.pillars.all())
        nodes = list(project.pxnodes.all())

        if pillars and nodes:
            try:
                agent: Any = PillarAlignmentAgent()
                data: dict[str, Any] = {
                    "pillars_section": self._format_pillars(pillars),
                    "nodes_section": self._format_nodes(nodes),
                }
                context = {"model_manager": self._model_manager, "data": data, "model_id": self._model_id}
                result = agent.execute(context)
                self._raise_if_rate_limited(result)
                if result.success and result.data:
                    agents_run.append("pillar_alignment")
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
                else:
                    agents_skipped["pillar_alignment"] = (
                        result.error.message if result.error else "agent returned no data"
                    )
            except RateLimitError:
                raise
            except Exception as e:
                agents_skipped["pillar_alignment"] = str(e)
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    "PillarAlignmentAgent",
                    e,
                )
        else:
            agents_skipped["pillar_alignment"] = (
                f"requires pillars and nodes "
                f"(pillars={len(pillars)}, nodes={len(nodes)})"
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
                context = {"model_manager": self._model_manager, "data": data, "model_id": self._model_id}
                result = agent.execute(context)
                self._raise_if_rate_limited(result)
                if result.success and result.data:
                    agents_run.append("node_coherence")
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
                else:
                    agents_skipped["node_coherence"] = (
                        result.error.message if result.error else "agent returned no data"
                    )
            except RateLimitError:
                raise
            except Exception as e:
                agents_skipped["node_coherence"] = str(e)
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    "NodeCoherenceAgent",
                    e,
                )
        else:
            agents_skipped["node_coherence"] = f"requires ≥2 nodes (nodes={len(nodes)})"

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
                context = {"model_manager": self._model_manager, "data": data, "model_id": self._model_id}
                result = agent.execute(context)
                self._raise_if_rate_limited(result)
                if result.success and result.data:
                    agents_run.append("terminology_consistency")
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
                else:
                    agents_skipped["terminology_consistency"] = (
                        result.error.message if result.error else "agent returned no data"
                    )
            except RateLimitError:
                raise
            except Exception as e:
                agents_skipped["terminology_consistency"] = str(e)
                logger.exception(
                    "Semantic check '%s' failed: %s",
                    "TerminologyConsistencyAgent",
                    e,
                )
        else:
            agents_skipped["terminology_consistency"] = (
                f"requires ≥2 nodes (nodes={len(nodes)})"
            )

        return findings, agents_run, agents_skipped

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

    def _raise_if_rate_limited(self, result: Any) -> None:
        if not result.success and result.error:
            if "rate limit" in (result.error.message or "").lower():
                raise RateLimitError(
                    message="Rate limit reached. Please wait and try again."
                )
