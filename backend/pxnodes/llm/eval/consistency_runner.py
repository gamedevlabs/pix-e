"""Run the Consistency agent against a loaded dataset and score it.

Bridges the live ConsistencyWorkflow to the pure metric core in ``metrics``:
runs the workflow N times for a given layer configuration, normalises each
reported finding into a :class:`Finding` (resolving ``entity_id`` to a node
name), matches it against the layer-appropriate trap set, and aggregates the
per-run results into mean ± std metrics.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from llm.providers.manager import ModelManager
from projects.models import Project
from pxnodes.llm.agents.consistency.workflow import ConsistencyWorkflow

from .metrics import AggregateMetrics, Finding, RunResult, Trap, aggregate, match_run

logger = logging.getLogger(__name__)

# Layer -> (run_structural, needs_model)
_LAYER_CONFIG = {
    "structural": (True, False),
    "semantic": (False, True),
    "all": (True, True),
}


# Pairwise categories whose finding message embeds the second node's name.
# Message formats (see consistency/workflow.py):
#   node_contradiction:        "[vs {node_b_name}] ..."
#   terminology_inconsistency: "['{term_a}' vs '{term_b}' in {node_b_name}] ..."
def extract_partner_name(category: str, message: str) -> Optional[str]:
    """Extract the second node's name from a pairwise finding's message.

    Returns None for non-pairwise categories or unparsable messages. Uses
    plain string scanning (not regex) so node/term names containing
    apostrophes — e.g. "Emperor's Basilica" — are handled correctly.
    """
    if not message.startswith("["):
        return None
    end = message.find("]")
    if end == -1:
        return None
    inner = message[1:end]
    if category == "node_contradiction" and inner.startswith("vs "):
        return inner[3:].strip()
    if category == "terminology_inconsistency":
        idx = inner.rfind(" in ")
        if idx != -1:
            return inner[idx + 4 :].strip()
    return None


def to_finding(
    category: str, entity_id: str, message: str, node_map: Dict[str, str]
) -> Finding:
    """Normalise a raw finding into a :class:`Finding`, resolving both the
    primary node (entity_id) and, for pairwise findings, the partner node."""
    return Finding(
        category=category,
        entity_id=entity_id,
        resolved_name=node_map.get(entity_id),
        message=message,
        partner_name=extract_partner_name(category, message),
    )


def load_traps(path: str | Path, layer: str) -> List[Trap]:
    """Load traps from the ground-truth JSON, filtered to the given layer.

    ``layer="all"`` returns every trap; otherwise only traps whose own
    ``layer`` matches (so each layer is scored against its own trap set, per
    the documented methodology).
    """
    data = json.loads(Path(path).read_text())
    traps = [
        Trap(
            id=t["id"],
            layer=t["layer"],
            category=t["category"],
            node=t.get("node"),
            partner=t.get("partner"),
        )
        for t in data["traps"]
    ]
    if layer != "all":
        traps = [t for t in traps if t.layer == layer]
    return traps


@dataclass
class ConsistencyEvalReport:
    layer: str
    model_id: Optional[str]
    min_confidence: float
    traps: List[Trap]
    run_results: List[RunResult] = field(default_factory=list)
    raw_findings: List[List[dict]] = field(default_factory=list)
    durations_s: List[float] = field(default_factory=list)
    metrics: Optional[AggregateMetrics] = None


def _node_name_map(project: Project) -> Dict[str, str]:
    return {str(n.id): n.name for n in project.pxnodes.all()}


def run_consistency_eval(
    project: Project,
    traps: Sequence[Trap],
    *,
    layer: str = "all",
    model_id: Optional[str] = None,
    min_confidence: float = 0.0,
    runs: int = 3,
    inter_run_sleep: float = 0.0,
) -> ConsistencyEvalReport:
    if layer not in _LAYER_CONFIG:
        raise ValueError(f"layer must be one of {sorted(_LAYER_CONFIG)}")

    run_structural, needs_model = _LAYER_CONFIG[layer]
    node_map = _node_name_map(project)

    report = ConsistencyEvalReport(
        layer=layer,
        model_id=model_id,
        min_confidence=min_confidence,
        traps=list(traps),
    )

    for i in range(runs):
        # A transient API failure (e.g. rate limit) on one run must not discard
        # all the others — record only successful runs and carry on.
        try:
            workflow = ConsistencyWorkflow(
                model_manager=ModelManager() if needs_model else None,
                min_confidence=min_confidence,
                run_structural=run_structural,
                model_id=model_id,
            )

            start = time.perf_counter()
            result = workflow.check_project(project)
            report.durations_s.append(time.perf_counter() - start)

            raw = [
                {
                    "severity": getattr(f.severity, "value", str(f.severity)),
                    "category": f.category,
                    "entity_id": f.entity_id,
                    "message": f.message,
                }
                for f in result.findings
            ]
            report.raw_findings.append(raw)

            findings = [
                to_finding(f.category, f.entity_id, f.message, node_map)
                for f in result.findings
            ]
            report.run_results.append(match_run(findings, traps))
        except Exception as e:
            logger.warning("Eval run %d/%d failed, skipping: %s", i + 1, runs, e)

        if inter_run_sleep and i < runs - 1:
            time.sleep(inter_run_sleep)

    if report.run_results:
        report.metrics = aggregate(report.run_results, traps)
    return report
