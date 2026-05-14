"""Tests for TerminologyConsistencyAgent finding-parsing logic in ConsistencyWorkflow."""

from unittest.mock import MagicMock, patch

from llm.types import AgentResult
from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.workflow import ConsistencyWorkflow


def _make_result(conflicts: list, success: bool = True) -> AgentResult:
    return AgentResult(
        agent_name="terminology_consistency",
        success=success,
        data={"conflicts": conflicts} if success else None,
        execution_time_ms=0,
    )


def _make_project(node_count: int = 2) -> MagicMock:
    project = MagicMock()
    project.pillars.all.return_value = []
    project.pxnodes.all.return_value = [
        MagicMock(id=f"n{i}", name=f"Node {i}", description=f"Desc {i}")
        for i in range(node_count)
    ]
    return project


PATCH_EXECUTE = (
    "pxnodes.llm.agents.consistency.semantic.terminology_consistency"
    ".TerminologyConsistencyAgent.execute"
)


class TestTerminologyConsistencyFindingParsing:
    def _workflow(self) -> ConsistencyWorkflow:
        return ConsistencyWorkflow(model_manager=MagicMock())

    def test_conflict_found_parsed_into_finding(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "term_a": "stamina bar",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "term_b": "energy meter",
                "message": "Both terms describe the same resource mechanic.",
                "confidence": 0.9,
            }
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings = self._workflow()._run_semantic_checks(_make_project())

        terminology_findings = [
            f for f in findings if f.category == "terminology_inconsistency"
        ]
        assert len(terminology_findings) == 1
        f = terminology_findings[0]
        assert f.category == "terminology_inconsistency"
        assert f.severity == FindingSeverity.INFO
        assert f.entity_id == "n0"
        assert "'stamina bar'" in f.message
        assert "'energy meter'" in f.message
        assert "Node 1" in f.message
        assert "Both terms describe the same resource mechanic." in f.message

    def test_no_conflict_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_result([])):
            findings = self._workflow()._run_semantic_checks(_make_project())

        terminology_findings = [
            f for f in findings if f.category == "terminology_inconsistency"
        ]
        assert terminology_findings == []

    def test_fewer_than_two_nodes_skips_agent(self):
        project = _make_project(node_count=1)

        with patch(PATCH_EXECUTE) as mock_exec:
            self._workflow()._run_semantic_checks(project)

        mock_exec.assert_not_called()

    def test_low_confidence_item_still_included(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "term_a": "mana",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "term_b": "magic points",
                "message": "Possibly the same spellcasting resource.",
                "confidence": 0.2,
            }
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings = self._workflow()._run_semantic_checks(_make_project())

        terminology_findings = [
            f for f in findings if f.category == "terminology_inconsistency"
        ]
        assert len(terminology_findings) == 1

    def test_multiple_conflicts_all_parsed(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "term_a": "stamina bar",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "term_b": "energy meter",
                "message": "Same resource mechanic, different names.",
                "confidence": 0.85,
            },
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "term_a": "skill tree",
                "node_b_id": "n2",
                "node_b_name": "Node 2",
                "term_b": "ability board",
                "message": "Both describe the progression system.",
                "confidence": 0.75,
            },
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings = self._workflow()._run_semantic_checks(
                _make_project(node_count=3)
            )

        terminology_findings = [
            f for f in findings if f.category == "terminology_inconsistency"
        ]
        assert len(terminology_findings) == 2
        assert terminology_findings[0].entity_id == "n0"
        assert terminology_findings[1].entity_id == "n0"

    def test_node_with_missing_description_handled_gracefully(self):
        project = _make_project(node_count=2)
        project.pxnodes.all.return_value = [
            MagicMock(id="n0", name="Node 0", description=""),
            MagicMock(id="n1", name="Node 1", description="Has a description"),
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result([])):
            findings = self._workflow()._run_semantic_checks(project)

        terminology_findings = [
            f for f in findings if f.category == "terminology_inconsistency"
        ]
        assert terminology_findings == []
