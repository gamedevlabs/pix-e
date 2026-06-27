"""Unit tests for the pure metric/matching core (no DB, no LLM)."""

from pxnodes.llm.eval.metrics import (
    Finding,
    Trap,
    aggregate,
    match_run,
)


def _f(category, name, entity_id="id-1"):
    return Finding(
        category=category, entity_id=entity_id, resolved_name=name, message=""
    )


P1 = Trap(id="P1", layer="semantic", category="pillar_misalignment", node="A")
C1 = Trap(
    id="C1",
    layer="semantic",
    category="node_contradiction",
    node="X",
    partner="Y",
)
T1 = Trap(id="T1", layer="semantic", category="terminology_inconsistency", node="Z")
S2 = Trap(id="S2", layer="structural", category="empty_name", node=None)


class TestMatchRun:
    def test_exact_true_positive(self):
        res = match_run([_f("pillar_misalignment", "A")], [P1])
        assert [t.id for t in res.tp] == ["P1"]
        assert res.fp == []
        assert res.fn == []

    def test_false_negative_when_not_reported(self):
        res = match_run([], [P1])
        assert res.tp == []
        assert [t.id for t in res.fn] == ["P1"]

    def test_false_positive_on_unmatched_finding(self):
        res = match_run([_f("pillar_misalignment", "Other")], [P1])
        assert res.tp == []
        assert len(res.fp) == 1
        assert [t.id for t in res.fn] == ["P1"]

    def test_category_mismatch_is_fp_and_fn(self):
        # T-trap node flagged as a contradiction: wrong category => FP + FN.
        res = match_run([_f("node_contradiction", "Z")], [T1])
        assert res.tp == []
        assert len(res.fp) == 1
        assert [t.id for t in res.fn] == ["T1"]

    def test_contradiction_matches_either_node_in_pair(self):
        # Finding resolves to the partner node Y — still a match for C1.
        res = match_run([_f("node_contradiction", "Y")], [C1])
        assert [t.id for t in res.tp] == ["C1"]

    def test_pairwise_matches_via_partner_name_when_trap_is_node_b(self):
        # node_A (entity_id) resolves to some other node, but the trap node Z
        # is node_B, carried in partner_name. Must still match T1.
        f = Finding(
            category="terminology_inconsistency",
            entity_id="id-other",
            resolved_name="Some Other Node",
            partner_name="Z",
        )
        res = match_run([f], [T1])
        assert [t.id for t in res.tp] == ["T1"]
        assert res.fp == []

    def test_unnamed_trap_matches_by_category(self):
        res = match_run([_f("empty_name", None)], [S2])
        assert [t.id for t in res.tp] == ["S2"]

    def test_hallucination_detected_and_counted_as_fp(self):
        # Node-referencing category but entity does not resolve => hallucination.
        f = _f("node_contradiction", None, entity_id="ghost")
        res = match_run([f], [C1])
        assert len(res.fp) == 1
        assert len(res.hallucinations) == 1
        assert [t.id for t in res.fn] == ["C1"]

    def test_each_trap_matched_at_most_once(self):
        findings = [_f("pillar_misalignment", "A"), _f("pillar_misalignment", "A")]
        res = match_run(findings, [P1])
        assert len(res.tp) == 1
        assert len(res.fp) == 1


class TestAggregate:
    def test_precision_recall_f1_single_run(self):
        res = match_run([_f("pillar_misalignment", "A")], [P1, T1])
        m = aggregate([res], [P1, T1])
        assert m.total_traps == 2
        assert m.precision_mean == 1.0  # 1 TP, 0 FP
        assert m.recall_mean == 0.5  # 1 of 2 traps
        assert round(m.f1_mean, 3) == round(2 * 1.0 * 0.5 / 1.5, 3)

    def test_mean_and_std_across_runs(self):
        r_hit = match_run([_f("pillar_misalignment", "A")], [P1])
        r_miss = match_run([], [P1])
        m = aggregate([r_hit, r_miss], [P1])
        assert m.recall_mean == 0.5
        assert m.recall_std == 0.5  # recalls are 1.0 and 0.0

    def test_per_category_recall(self):
        # P1 found in both runs, T1 in neither.
        r1 = match_run([_f("pillar_misalignment", "A")], [P1, T1])
        r2 = match_run([_f("pillar_misalignment", "A")], [P1, T1])
        m = aggregate([r1, r2], [P1, T1])
        assert m.per_category_recall["pillar_misalignment"] == 1.0
        assert m.per_category_recall["terminology_inconsistency"] == 0.0


class TestPartnerExtraction:
    """node_B extraction from the message (the bug that caused terminology=0)."""

    def test_terminology_partner_with_apostrophe(self):
        from pxnodes.llm.eval.consistency_runner import extract_partner_name

        msg = (
            "['Emperor's Cathedral' vs 'Emperor's Basilica' "
            "in Mission Objectives Overview] ..."
        )
        assert (
            extract_partner_name("terminology_inconsistency", msg)
            == "Mission Objectives Overview"
        )

    def test_contradiction_partner(self):
        from pxnodes.llm.eval.consistency_runner import extract_partner_name

        msg = "[vs A floating gift] The node states the player begins with two ships."
        assert extract_partner_name("node_contradiction", msg) == "A floating gift"

    def test_non_pairwise_returns_none(self):
        from pxnodes.llm.eval.consistency_runner import extract_partner_name

        assert (
            extract_partner_name("pillar_misalignment", "[pillar 3] misaligned") is None
        )
        assert (
            extract_partner_name("orphaned_node", "Node 'X' is not in any chart.")
            is None
        )
