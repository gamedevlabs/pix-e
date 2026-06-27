"""Unit tests for the symbolic Stage 2 of the neuro-symbolic terminology check.

`group_into_findings` is pure and deterministic — no LLM, no DB.
"""

from pxnodes.llm.agents.consistency.semantic.terminology_neurosymbolic import (
    group_into_findings,
)


def _m(node_id, node_name, term, concept):
    return {
        "node_id": node_id,
        "node_name": node_name,
        "term": term,
        "concept": concept,
    }


class TestGroupIntoFindings:
    def test_single_term_per_concept_is_consistent(self):
        mentions = [
            _m("n1", "A", "peasants", "peasant"),
            _m("n2", "B", "peasants", "peasant"),
        ]
        assert group_into_findings(mentions) == []

    def test_same_concept_different_terms_is_flagged(self):
        # The T1 scenario: serfs (1 node) vs peasants (3 nodes).
        mentions = [
            _m("serf-node", "Settlement Overview", "serfs", "peasant"),
            _m("n2", "Safe as Houses", "peasants", "peasant"),
            _m("n3", "More Peasant houses", "peasants", "peasant"),
            _m("n4", "Victory Condition", "peasants", "peasant"),
        ]
        findings = group_into_findings(mentions)
        assert len(findings) == 1
        f = findings[0]
        assert f.category == "terminology_inconsistency"
        # The variant ("serfs") node is entity_id; the established term node is in
        # the message — so the evaluation matcher resolves the trap node either way.
        assert f.entity_id == "serf-node"
        assert "serfs" in f.message and "peasants" in f.message

    def test_most_frequent_term_is_treated_as_established(self):
        # "trade ship" used twice, "merchant vessel" once -> variant is the vessel.
        mentions = [
            _m("a", "A floating gift", "trade ship", "player ship"),
            _m("b", "Player's Ship State", "trade ship", "player ship"),
            _m("variant", "Map Exploration State", "merchant vessel", "player ship"),
        ]
        findings = group_into_findings(mentions)
        assert len(findings) == 1
        assert findings[0].entity_id == "variant"

    def test_three_terms_yield_two_findings(self):
        mentions = [
            _m("n1", "A", "peasants", "peasant"),
            _m("n1b", "A2", "peasants", "peasant"),
            _m("n2", "B", "serfs", "peasant"),
            _m("n3", "C", "villagers", "peasant"),
        ]
        findings = group_into_findings(mentions)
        assert len(findings) == 2
        assert {f.entity_id for f in findings} == {"n2", "n3"}

    def test_concept_key_is_case_and_whitespace_insensitive(self):
        mentions = [
            _m("n1", "A", "serfs", " Peasant "),
            _m("n2", "B", "peasants", "peasant"),
        ]
        assert len(group_into_findings(mentions)) == 1

    def test_same_term_different_case_is_not_a_variant(self):
        mentions = [
            _m("n1", "A", "Peasants", "peasant"),
            _m("n2", "B", "peasants", "peasant"),
        ]
        assert group_into_findings(mentions) == []

    def test_empty_concept_or_term_is_skipped(self):
        mentions = [
            _m("n1", "A", "serfs", ""),
            _m("n2", "B", "", "peasant"),
            _m("n3", "C", "peasants", "peasant"),
        ]
        assert group_into_findings(mentions) == []


class TestPrecisionFilters:
    """Symbolic filters that suppress prose/refinement false positives."""

    def test_substring_refinement_is_not_flagged(self):
        # "cathedral" is a subset of "Imperial cathedral" -> a refinement.
        mentions = [
            _m("n1", "A", "Imperial cathedral", "cathedral"),
            _m("n2", "B", "Imperial cathedral", "cathedral"),
            _m("n3", "C", "cathedral", "cathedral"),
        ]
        assert group_into_findings(mentions) == []

    def test_token_subset_full_vs_short_name_not_flagged(self):
        mentions = [
            _m("n1", "A", "Lord Richard Northburgh", "npc_lord"),
            _m("n2", "B", "Lord Northburgh", "npc_lord"),
        ]
        assert group_into_findings(mentions) == []

    def test_article_prefixed_prose_term_is_dropped(self):
        # "the island" is dropped -> only the canonical "Falconstone" remains.
        mentions = [
            _m("n1", "A", "Falconstone", "island"),
            _m("n2", "B", "the island", "island"),
        ]
        assert group_into_findings(mentions) == []

    def test_long_descriptive_phrase_is_dropped(self):
        mentions = [
            _m("n1", "A", "Falconstone", "island"),
            _m("n2", "B", "Lord Northburgh's second island", "island"),
        ]
        assert group_into_findings(mentions) == []

    def test_real_near_synonyms_still_flagged(self):
        # The filters must NOT suppress genuine traps (T4-style).
        mentions = [
            _m("n1", "A", "Gold coins", "currency"),
            _m("n2", "B", "Gold coins", "currency"),
            _m("n3", "C", "gold pieces", "currency"),
        ]
        findings = group_into_findings(mentions)
        assert len(findings) == 1
        assert findings[0].entity_id == "n3"
