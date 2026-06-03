"""Run the Change Propagation agent against frozen scenarios and score it.

Mirrors the consistency runner. Each scenario is a hypothetical edit to one node
(explicit old + new description, so the changed node's dataset state is
irrelevant) with a ground-truth set of *affected* node IDs. For each scenario we
run a mode N times, collect the flagged affected node IDs, and match them against
the expected set — reusing the pure metric core in ``metrics``.

Three modes:
- "flat":      LLM, all other project nodes flat in the prompt (baseline).
- "graph":     LLM, graph-aware BFS over PxChartEdge (use_graph_context).
- "neighbors": NO LLM — just return all k-hop chart neighbours of the changed
               node. Isolates how much the graph structure alone contributes vs
               the LLM's semantic reasoning.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set

from llm.providers.manager import ModelManager
from projects.models import Project
from pxnodes.llm.agents.change_propagation.workflow import ChangePropagationWorkflow
from pxnodes.models import PxNode

from .metrics import AggregateMetrics, Finding, RunResult, Trap, aggregate, match_run

logger = logging.getLogger(__name__)

MODES = ("flat", "graph", "semantic", "neighbors")
_AFFECTED = "affected"


def load_cp_scenarios(path: str | Path) -> List[Dict[str, Any]]:
    return json.loads(Path(path).read_text())["scenarios"]


def _traps_for(scenario: Dict[str, Any]) -> List[Trap]:
    # Match by node_id (robust against duplicate node names like "Mission I").
    return [
        Trap(id=a["node_id"], layer="cp", category=_AFFECTED, node=a["node_id"])
        for a in scenario["expected_affected"]
    ]


def _k_hop_neighbor_ids(changed_node_id: str, max_depth: int) -> List[str]:
    """All chart neighbours within ``max_depth`` hops (predecessors+successors),
    using the workflow's edge traversal. No LLM."""
    wf = ChangePropagationWorkflow()
    visited: Set[str] = {str(changed_node_id)}
    frontier: List[str] = [str(changed_node_id)]
    collected: List[str] = []
    for _ in range(max_depth):
        next_frontier: List[str] = []
        for nid in frontier:
            neighbours = wf._get_1hop_neighbors(nid) or []
            for nb in neighbours:
                if nb["id"] not in visited:
                    visited.add(nb["id"])
                    collected.append(nb["id"])
                    next_frontier.append(nb["id"])
        frontier = next_frontier
        if not frontier:
            break
    return collected


@dataclass
class ScenarioReport:
    scenario_id: str
    title: str
    n_expected: int
    run_results: List[RunResult] = field(default_factory=list)
    flagged_ids: List[List[str]] = field(default_factory=list)
    durations_s: List[float] = field(default_factory=list)
    metrics: Optional[AggregateMetrics] = None


@dataclass
class CpEvalReport:
    mode: str
    model_id: Optional[str]
    scenarios: List[ScenarioReport] = field(default_factory=list)


def _flagged_ids_for_run(
    scenario: Dict[str, Any],
    project: Project,
    changed_node: PxNode,
    mode: str,
    model_manager: Optional[ModelManager],
    model_id: Optional[str],
    min_confidence: float,
    max_depth: int,
    semantic_top_k: Optional[int] = None,
) -> List[str]:
    if mode == "neighbors":
        return _k_hop_neighbor_ids(scenario["changed_node_id"], max_depth)

    workflow = ChangePropagationWorkflow(model_manager=model_manager)
    report = workflow.check_change(
        project=project,
        changed_node=changed_node,
        old_description=scenario["old_description"],
        new_description=scenario["new_description"],
        min_confidence=min_confidence,
        use_graph_context=(mode == "graph"),
        max_depth=max_depth,
        model_id=model_id,
        semantic_top_k=semantic_top_k if mode == "semantic" else None,
    )
    return [f.affected_node_id for f in report.findings]


def run_cp_eval(
    project: Project,
    scenarios: Sequence[Dict[str, Any]],
    *,
    mode: str = "flat",
    model_id: Optional[str] = None,
    min_confidence: float = 0.5,
    runs: int = 3,
    max_depth: int = 3,
    semantic_top_k: int = 10,
    inter_run_sleep: float = 0.0,
) -> CpEvalReport:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")

    # The neighbours baseline is deterministic — one run suffices.
    effective_runs = 1 if mode == "neighbors" else runs
    needs_model = mode != "neighbors"

    report = CpEvalReport(mode=mode, model_id=model_id if needs_model else None)

    for scenario in scenarios:
        traps = _traps_for(scenario)
        sr = ScenarioReport(
            scenario_id=scenario["id"],
            title=scenario["title"],
            n_expected=len(traps),
        )
        changed_node = PxNode.objects.get(id=scenario["changed_node_id"])

        for i in range(effective_runs):
            try:
                start = time.perf_counter()
                flagged = _flagged_ids_for_run(
                    scenario,
                    project,
                    changed_node,
                    mode,
                    ModelManager() if needs_model else None,
                    model_id,
                    min_confidence,
                    max_depth,
                    semantic_top_k,
                )
                sr.durations_s.append(time.perf_counter() - start)
                sr.flagged_ids.append(flagged)
                findings = [
                    Finding(category=_AFFECTED, entity_id=fid, resolved_name=fid)
                    for fid in flagged
                ]
                sr.run_results.append(match_run(findings, traps))
            except Exception as e:
                logger.warning(
                    "CP run %d/%d for scenario %s failed: %s",
                    i + 1,
                    effective_runs,
                    scenario["id"],
                    e,
                )
            if inter_run_sleep and i < effective_runs - 1:
                time.sleep(inter_run_sleep)

        if sr.run_results:
            sr.metrics = aggregate(sr.run_results, traps)
        report.scenarios.append(sr)

    return report
