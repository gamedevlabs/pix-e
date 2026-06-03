import logging
from typing import Any, Dict, List, Optional, Set

from game_concept.models import Project
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .agent import ChangePropagationAgent
from .schemas import PropagationFinding, PropagationReport

logger = logging.getLogger(__name__)


class ChangePropagationWorkflow:
    """Identifies PxNodes in a project that are semantically affected by a
    description change to a single node."""

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
    ) -> None:
        self._model_manager = model_manager

    def check_change(
        self,
        project: Project,
        changed_node: PxNode,
        old_description: str,
        new_description: str,
        min_confidence: float = 0.5,
        use_graph_context: bool = False,
        max_depth: int = 3,
        model_id: Optional[str] = None,
    ) -> PropagationReport:
        if self._model_manager is None:
            raise ValueError(
                "ChangePropagationWorkflow requires a ModelManager — "
                "the Change Propagation Agent is entirely LLM-driven."
            )

        findings: List[PropagationFinding] = []
        try:
            if use_graph_context:
                findings = self._run_iterative_graph_propagation(
                    project=project,
                    changed_node=changed_node,
                    old_description=old_description,
                    new_description=new_description,
                    min_confidence=min_confidence,
                    max_depth=max_depth,
                    model_id=model_id,
                )
            else:
                other_nodes = list(project.pxnodes.exclude(id=changed_node.id))
                agent = ChangePropagationAgent(
                    model_manager=self._model_manager,
                    min_confidence=min_confidence,
                    model_id=model_id,
                )
                findings = agent.analyze_change(
                    changed_node=changed_node,
                    old_description=old_description,
                    new_description=new_description,
                    other_nodes=other_nodes,
                    use_graph_context=False,
                )
        except Exception as e:
            logger.exception("ChangePropagationWorkflow failed: %s", e)

        return PropagationReport(
            changed_node_id=str(changed_node.id),
            findings=findings,
        )

    def _get_1hop_neighbors(
        self, node_id: Any
    ) -> Optional[List[Dict[str, Any]]]:
        """Get direct PREDECESSOR and SUCCESSOR neighbors of a node via PxChartEdge.

        Returns None if the node is not placed in any chart.
        Returns an empty list if placed but has no connected neighbors.
        """
        from pxcharts.models import PxChartContainer, PxChartEdge

        containers = list(PxChartContainer.objects.filter(content_id=node_id))
        if not containers:
            return None

        container_ids = {c.id for c in containers}
        nid_str = str(node_id)
        node_rel: Dict[str, str] = {}

        def register(nid: Any, rel: str) -> None:
            sid = str(nid)
            if sid != nid_str and sid not in node_rel:
                node_rel[sid] = rel

        for pred_id in PxChartEdge.objects.filter(
            target_id__in=container_ids,
            source__content__isnull=False,
        ).values_list("source__content_id", flat=True):
            register(pred_id, "PREDECESSOR")

        for succ_id in PxChartEdge.objects.filter(
            source_id__in=container_ids,
            target__content__isnull=False,
        ).values_list("target__content_id", flat=True):
            register(succ_id, "SUCCESSOR")

        if not node_rel:
            return []

        nodes_by_id = {
            str(n.id): n
            for n in PxNode.objects.filter(id__in=node_rel.keys())
        }
        return [
            {
                "id": nid,
                "name": nodes_by_id[nid].name,
                "description": nodes_by_id[nid].description or "",
                "relationship": rel,
            }
            for nid, rel in node_rel.items()
            if nid in nodes_by_id
        ]

    def _run_iterative_graph_propagation(
        self,
        project: Project,
        changed_node: PxNode,
        old_description: str,
        new_description: str,
        min_confidence: float,
        max_depth: int,
        model_id: Optional[str] = None,
    ) -> List[PropagationFinding]:
        agent = ChangePropagationAgent(
            model_manager=self._model_manager,
            min_confidence=min_confidence,
            model_id=model_id,
        )

        all_findings: Dict[str, PropagationFinding] = {}
        visited: Set[str] = {str(changed_node.id)}

        # Round 1: direct 1-hop neighbors of the changed node
        neighbors = self._get_1hop_neighbors(changed_node.id)
        if neighbors is None:
            logger.warning(
                "[BFS] Node '%s' not in any chart — falling back to flat list.",
                changed_node.name,
            )
            other_nodes = list(project.pxnodes.exclude(id=changed_node.id))
            return agent.analyze_change(
                changed_node=changed_node,
                old_description=old_description,
                new_description=new_description,
                other_nodes=other_nodes,
                use_graph_context=False,
            )

        if not neighbors:
            logger.warning("[BFS] Node '%s' has no graph neighbors.", changed_node.name)
            return []

        logger.warning(
            "[BFS] Round 1: %d neighbors of '%s'",
            len(neighbors), changed_node.name,
        )

        round1_findings = agent.analyze_change(
            changed_node=changed_node,
            old_description=old_description,
            new_description=new_description,
            other_nodes=neighbors,
            use_graph_context=True,
        )

        frontier: List[PropagationFinding] = []
        for f in round1_findings:
            nid = f.affected_node_id
            visited.add(nid)
            all_findings[nid] = f
            frontier.append(f)

        # Rounds 2..max_depth
        for depth in range(2, max_depth + 1):
            if not frontier:
                break

            next_frontier: List[PropagationFinding] = []
            for parent_finding in frontier:
                parent_id = parent_finding.affected_node_id
                parent_neighbors = self._get_1hop_neighbors(parent_id)
                if not parent_neighbors:
                    continue

                unseen = [n for n in parent_neighbors if n["id"] not in visited]
                if not unseen:
                    continue

                logger.warning(
                    "[BFS] Round %d: expanding '%s' → %d unseen neighbors",
                    depth, parent_finding.affected_node_name, len(unseen),
                )

                try:
                    parent_node = PxNode.objects.get(id=parent_id)
                except PxNode.DoesNotExist:
                    continue

                new_findings = agent.analyze_transitive_change(
                    changed_node_name=changed_node.name,
                    old_description=old_description,
                    new_description=new_description,
                    affected_node_name=parent_node.name,
                    affected_node_description=parent_node.description or "",
                    reason_chain=parent_finding.reason,
                    neighbors=unseen,
                )

                for f in new_findings:
                    nid = f.affected_node_id
                    visited.add(nid)
                    if nid not in all_findings:
                        all_findings[nid] = f
                        next_frontier.append(f)

            frontier = next_frontier

        logger.warning("[BFS] Done. Total findings: %d", len(all_findings))
        return list(all_findings.values())
