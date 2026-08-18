import logging
import math
from typing import Any, Dict, List, Optional, Set

from game_concept.models import Project
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .agent import ChangePropagationAgent
from .schemas import PropagationFinding, PropagationReport

logger = logging.getLogger(__name__)


def _cosine(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


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
        pairwise: bool = False,
        neighbors: bool = False,
        max_depth: int = 3,
        model_id: Optional[str] = None,
        semantic_top_k: Optional[int] = None,
    ) -> PropagationReport:
        if self._model_manager is None:
            raise ValueError(
                "ChangePropagationWorkflow requires a ModelManager — "
                "the Change Propagation Agent is entirely LLM-driven."
            )

        findings: List[PropagationFinding] = []
        try:
            if use_graph_context:
                findings = self._run_graph_propagation(
                    project=project,
                    changed_node=changed_node,
                    old_description=old_description,
                    new_description=new_description,
                    min_confidence=min_confidence,
                    max_depth=max_depth,
                    model_id=model_id,
                )
            elif pairwise:
                findings = self._run_pairwise_propagation(
                    project=project,
                    changed_node=changed_node,
                    old_description=old_description,
                    new_description=new_description,
                    min_confidence=min_confidence,
                    model_id=model_id,
                )
            elif neighbors:
                findings = self._run_neighbors_baseline(
                    changed_node=changed_node,
                    max_depth=max_depth,
                )
            else:
                if semantic_top_k:
                    other_nodes = self._semantic_topk_nodes(
                        project=project,
                        changed_node=changed_node,
                        query_text=new_description,
                        k=semantic_top_k,
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

    def _run_pairwise_propagation(
        self,
        project: Project,
        changed_node: PxNode,
        old_description: str,
        new_description: str,
        min_confidence: float,
        model_id: Optional[str] = None,
    ) -> List[PropagationFinding]:
        """Pointwise counterpart to the flat baseline.

        Instead of a single LLM call over all candidates at once (flat=listwise),
        ask the LLM once *per* other node in isolation ("is THIS node affected?")
        via a dedicated strict binary prompt (see ``analyze_pair``). Retrieval is
        identical to flat (every other node); the call granularity is pointwise.
        Each candidate gets the model's full, undiluted attention (no 'lost in the
        middle') at the price of O(N) LLM calls per change. The strict prompt
        counters the yes-bias that a naive single-item flat prompt produced.
        """
        assert self._model_manager is not None
        agent = ChangePropagationAgent(
            model_manager=self._model_manager,
            min_confidence=min_confidence,
            model_id=model_id,
        )
        others = list(project.pxnodes.exclude(id=changed_node.id))

        # Dedup by affected node id, keeping the highest-confidence finding —
        # mirrors the BFS path so downstream scoring sees a unique affected set.
        all_findings: Dict[str, PropagationFinding] = {}
        for node in others:
            for f in agent.analyze_pair(
                changed_node=changed_node,
                old_description=old_description,
                new_description=new_description,
                candidate=node,
            ):
                existing = all_findings.get(f.affected_node_id)
                if existing is None or f.confidence > existing.confidence:
                    all_findings[f.affected_node_id] = f
        return list(all_findings.values())

    def _run_neighbors_baseline(
        self,
        changed_node: PxNode,
        max_depth: int,
    ) -> List[PropagationFinding]:
        """Non-LLM structural baseline: flag every chart neighbour within
        ``max_depth`` hops of the changed node as 'affected', with no semantic
        analysis. Mirrors the eval harness's ``neighbors`` mode so the frontend
        can show the pure-graph baseline alongside the LLM arms. Findings carry a
        fixed confidence of 1.0 and an explanatory reason (there is no model
        judgement to score)."""
        visited: Set[str] = {str(changed_node.id)}
        frontier: List[str] = [str(changed_node.id)]
        collected: List[str] = []
        for _ in range(max_depth):
            next_frontier: List[str] = []
            for nid in frontier:
                for nb in self._get_1hop_neighbors(nid) or []:
                    if nb["id"] not in visited:
                        visited.add(nb["id"])
                        collected.append(nb["id"])
                        next_frontier.append(nb["id"])
            frontier = next_frontier
            if not frontier:
                break

        if not collected:
            return []

        nodes_by_id = {str(n.id): n for n in PxNode.objects.filter(id__in=collected)}
        findings: List[PropagationFinding] = []
        for nid in collected:
            node = nodes_by_id.get(nid)
            if node is None:
                continue
            findings.append(
                PropagationFinding(
                    affected_node_id=nid,
                    affected_node_name=node.name,
                    reason=(
                        f"Structural baseline: chart neighbour within "
                        f"{max_depth} hop(s) of the changed node "
                        f"(no semantic analysis performed)."
                    ),
                    confidence=1.0,
                    suggested_action="Review whether this neighbour is affected.",
                )
            )
        return findings

    def _semantic_topk_nodes(
        self,
        project: Project,
        changed_node: PxNode,
        query_text: str,
        k: int,
    ) -> List[PxNode]:
        """Embedding-based retrieval: return the ``k`` PxNodes whose text is most
        cosine-similar to the changed node's new description. This is the
        'semantic-RAG' retrieval arm (vs. flat=all nodes, graph=BFS neighbours)."""
        others = list(project.pxnodes.exclude(id=changed_node.id))
        if not others or k <= 0:
            return others

        # Lazy import: keeps the embedding/OpenAI dependency off the module path
        # for callers that never use the semantic arm.
        from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator

        generator = OpenAIEmbeddingGenerator()
        query_vec = generator.generate_embedding(f"{changed_node.name}\n{query_text}")
        node_texts = [f"{n.name}\n{n.description or ''}" for n in others]
        node_vecs = generator.generate_embeddings_batch(node_texts)

        ranked = sorted(
            zip(others, node_vecs),
            key=lambda pair: _cosine(query_vec, pair[1]),
            reverse=True,
        )
        return [node for node, _ in ranked[:k]]

    def _get_1hop_neighbors(self, node_id: Any) -> Optional[List[Dict[str, Any]]]:
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
            str(n.id): n for n in PxNode.objects.filter(id__in=node_rel.keys())
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

    def _run_graph_propagation(
        self,
        project: Project,
        changed_node: PxNode,
        old_description: str,
        new_description: str,
        min_confidence: float,
        max_depth: int,
        model_id: Optional[str] = None,
    ) -> List[PropagationFinding]:
        """Graph-aware retrieval in retrieve-then-judge form.

        Collect the changed node's chart neighbourhood up to ``max_depth`` hops with
        a pure BFS over PxChartEdge (no LLM), then judge that whole candidate set in a
        *single* LLM pass. This mirrors the flat and semantic arms (retrieve a
        candidate set, then one call) and differs only in *how* the set is
        retrieved — graph neighbourhood vs. all nodes vs. embedding top-k. Cost is one
        call per change at any depth, so it scales to dense dependency graphs, unlike
        an iterative per-hop expansion (one call per expanded node) which cascades.
        """
        assert self._model_manager is not None
        agent = ChangePropagationAgent(
            model_manager=self._model_manager,
            min_confidence=min_confidence,
            model_id=model_id,
        )

        # A node not placed in any chart has no neighbourhood → fall back to flat.
        first_hop = self._get_1hop_neighbors(changed_node.id)
        if first_hop is None:
            logger.warning(
                "[graph] Node '%s' not in any chart — falling back to flat list.",
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

        # BFS to max_depth, collecting the neighbourhood as candidate dicts.
        visited: Set[str] = {str(changed_node.id)}
        collected: Dict[str, Dict[str, Any]] = {}
        frontier: List[Any] = [changed_node.id]
        for _ in range(max_depth):
            next_frontier: List[Any] = []
            for nid in frontier:
                for nb in self._get_1hop_neighbors(nid) or []:
                    if nb["id"] not in visited:
                        visited.add(nb["id"])
                        collected[nb["id"]] = nb
                        next_frontier.append(nb["id"])
            frontier = next_frontier
            if not frontier:
                break

        if not collected:
            logger.warning(
                "[graph] Node '%s' has no graph neighbours.", changed_node.name
            )
            return []

        logger.warning(
            "[graph] '%s': %d-node neighbourhood within %d hop(s), single LLM pass.",
            changed_node.name,
            len(collected),
            max_depth,
        )
        return agent.analyze_change(
            changed_node=changed_node,
            old_description=old_description,
            new_description=new_description,
            other_nodes=list(collected.values()),
            use_graph_context=True,
        )
