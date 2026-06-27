"""Pure metric and matching logic for the evaluation harness.

Deliberately free of Django and LLM dependencies so it can be unit-tested in
isolation and reasoned about independently of how findings are produced.

Matching follows the methodology documented in the ground-truth sheet:
- A reported finding is a True Positive (TP) if it matches an as-yet-unmatched
  trap of the same category whose node matches.
- A finding that matches no trap is a False Positive (FP).
- A trap that no finding matched is a False Negative (FN).
- A node-referencing finding whose entity cannot be resolved to a real node in
  the dataset is additionally flagged as a hallucination (and counts as an FP).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# Categories whose entity_id is expected to reference a PxNode. A finding in one
# of these categories whose entity_id does not resolve to a real node is treated
# as a hallucinated reference.
NODE_REFERENCING_CATEGORIES = {
    "empty_description",
    "empty_name",
    "duplicate_node_name",
    "orphaned_node",
    "pillar_misalignment",
    "node_contradiction",
    "terminology_inconsistency",
}


@dataclass(frozen=True)
class Trap:
    """A single labelled defect in the dataset (one row of the ground truth)."""

    id: str
    layer: str  # "structural" | "semantic"
    category: str
    node: Optional[str] = None  # canonical node name; None if not name-matchable
    partner: Optional[str] = None  # second node for pairwise traps (contradictions)


@dataclass(frozen=True)
class Finding:
    """A finding reported by an agent, normalised for matching.

    `resolved_name` is the name the entity_id resolves to in the loaded dataset,
    or None if it does not resolve to a known node.
    """

    category: str
    entity_id: str
    resolved_name: Optional[str]
    message: str = ""
    # For pairwise findings (contradiction/terminology) the trap node is often
    # the *second* node, whose name is carried in the message rather than in
    # entity_id. partner_name holds that second node's name when applicable.
    partner_name: Optional[str] = None

    @property
    def is_hallucinated(self) -> bool:
        return (
            self.category in NODE_REFERENCING_CATEGORIES and self.resolved_name is None
        )


@dataclass
class RunResult:
    """Outcome of matching one run's findings against the trap set."""

    tp: List[Trap] = field(default_factory=list)
    fp: List[Finding] = field(default_factory=list)
    fn: List[Trap] = field(default_factory=list)
    hallucinations: List[Finding] = field(default_factory=list)

    @property
    def precision(self) -> float:
        denom = len(self.tp) + len(self.fp)
        return len(self.tp) / denom if denom else 0.0

    def recall(self, total_traps: int) -> float:
        return len(self.tp) / total_traps if total_traps else 0.0

    def f1(self, total_traps: int) -> float:
        p, r = self.precision, self.recall(total_traps)
        return 2 * p * r / (p + r) if (p + r) else 0.0


def _trap_matches(finding: Finding, trap: Trap) -> bool:
    if finding.category != trap.category:
        return False
    if trap.node is None:
        # Not name-matchable (e.g. empty_name): category match is sufficient.
        return True
    trap_names = {trap.node}
    if trap.partner:
        trap_names.add(trap.partner)
    # A pairwise finding implicates two nodes; match if EITHER side of the
    # finding (node_A via entity_id, or node_B via the message) is in the trap.
    finding_names = {
        name for name in (finding.resolved_name, finding.partner_name) if name
    }
    return bool(trap_names & finding_names)


def match_run(findings: Sequence[Finding], traps: Sequence[Trap]) -> RunResult:
    """Match one run's findings against the trap set (greedy, each trap once)."""
    result = RunResult(fn=list(traps))
    unmatched = list(traps)

    for finding in findings:
        matched: Optional[Trap] = None
        for trap in unmatched:
            if _trap_matches(finding, trap):
                matched = trap
                break
        if matched is not None:
            result.tp.append(matched)
            unmatched.remove(matched)
        else:
            result.fp.append(finding)
            if finding.is_hallucinated:
                result.hallucinations.append(finding)

    result.fn = unmatched
    return result


@dataclass
class AggregateMetrics:
    """Mean ± std of P/R/F1 across runs, plus per-category recall."""

    runs: int
    total_traps: int
    precision_mean: float
    precision_std: float
    recall_mean: float
    recall_std: float
    f1_mean: float
    f1_std: float
    per_category_recall: Dict[str, float]
    avg_false_positives: float
    avg_hallucinations: float


def _mean_std(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    var = sum((v - mean) ** 2 for v in values) / len(values)
    return mean, math.sqrt(var)


def aggregate(
    run_results: Sequence[RunResult], traps: Sequence[Trap]
) -> AggregateMetrics:
    """Aggregate per-run results into mean ± std metrics over all runs."""
    total = len(traps)
    precisions = [r.precision for r in run_results]
    recalls = [r.recall(total) for r in run_results]
    f1s = [r.f1(total) for r in run_results]

    # Per-category recall: fraction of runs in which each trap was found,
    # averaged within its category.
    categories = sorted({t.category for t in traps})
    per_cat: Dict[str, float] = {}
    for cat in categories:
        cat_traps = [t for t in traps if t.category == cat]
        if not cat_traps:
            continue
        found_fractions = []
        for t in cat_traps:
            hits = sum(1 for r in run_results if t in r.tp)
            found_fractions.append(hits / len(run_results) if run_results else 0.0)
        per_cat[cat] = sum(found_fractions) / len(found_fractions)

    p_mean, p_std = _mean_std(precisions)
    r_mean, r_std = _mean_std(recalls)
    f_mean, f_std = _mean_std(f1s)

    avg_fp = (
        sum(len(r.fp) for r in run_results) / len(run_results) if run_results else 0.0
    )
    avg_hall = (
        sum(len(r.hallucinations) for r in run_results) / len(run_results)
        if run_results
        else 0.0
    )

    return AggregateMetrics(
        runs=len(run_results),
        total_traps=total,
        precision_mean=p_mean,
        precision_std=p_std,
        recall_mean=r_mean,
        recall_std=r_std,
        f1_mean=f_mean,
        f1_std=f_std,
        per_category_recall=per_cat,
        avg_false_positives=avg_fp,
        avg_hallucinations=avg_hall,
    )
