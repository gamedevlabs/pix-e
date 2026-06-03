from unittest.mock import MagicMock, patch

from llm.types import AgentResult
from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.workflow import ConsistencyWorkflow


def _make_result(contradictions: list, success: bool = True) -> AgentResult:
    return AgentResult(
        agent_name="node_coherence",
        success=success,
        data={"contradictions": contradictions} if success else None,
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
    "pxnodes.llm.agents.consistency.semantic.node_coherence"
    ".NodeCoherenceAgent.execute"
)


class TestNodeCoherenceFindingParsing:
    def _workflow(self) -> ConsistencyWorkflow:
        return ConsistencyWorkflow(model_manager=MagicMock())

    def test_contradicting_pair_parsed_into_finding(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "message": "Turn-based vs real-time combat",
                "confidence": 0.9,
            }
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "node_contradiction"
        assert f.severity == FindingSeverity.WARNING
        assert f.entity_id == "n0"
        assert "[vs Node 1]" in f.message
        assert "Turn-based vs real-time combat" in f.message

    def test_no_contradiction_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_result([])):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []

    def test_fewer_than_two_nodes_skips_agent(self):
        project = _make_project(node_count=1)

        with patch(PATCH_EXECUTE) as mock_exec:
            findings, _, _ = self._workflow()._run_semantic_checks(project)

        mock_exec.assert_not_called()
        assert findings == []

    def test_low_confidence_item_still_included(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "message": "Possible contradiction",
                "confidence": 0.2,
            }
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert len(findings) == 1

    def test_multiple_contradictions_all_parsed(self):
        raw = [
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "node_b_id": "n1",
                "node_b_name": "Node 1",
                "message": "Contradiction A",
                "confidence": 0.8,
            },
            {
                "node_a_id": "n0",
                "node_a_name": "Node 0",
                "node_b_id": "n2",
                "node_b_name": "Node 2",
                "message": "Contradiction B",
                "confidence": 0.7,
            },
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings, _, _ = self._workflow()._run_semantic_checks(
                _make_project(node_count=3)
            )

        assert len(findings) == 2
        assert findings[0].entity_id == "n0"
        assert findings[1].entity_id == "n0"

    def test_node_with_empty_description_handled_gracefully(self):
        project = _make_project(node_count=2)
        project.pxnodes.all.return_value = [
            MagicMock(id="n0", name="Node 0", description=""),
            MagicMock(id="n1", name="Node 1", description="Has description"),
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result([])):
            findings, _, _ = self._workflow()._run_semantic_checks(project)

        assert findings == []

    def test_agent_failure_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_result([], success=False)):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []

    def test_agent_exception_returns_empty(self):
        with patch(PATCH_EXECUTE, side_effect=RuntimeError("LLM unavailable")):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []
