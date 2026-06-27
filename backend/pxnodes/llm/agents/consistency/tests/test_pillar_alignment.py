from unittest.mock import MagicMock, patch

from llm.types import AgentResult
from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.workflow import ConsistencyWorkflow


def _make_result(findings_data: list, success: bool = True) -> AgentResult:
    return AgentResult(
        agent_name="pillar_alignment",
        success=success,
        data={"findings": findings_data} if success else None,
        execution_time_ms=0,
    )


def _make_project(pillar_count: int = 1, node_count: int = 1) -> MagicMock:
    project = MagicMock()
    project.pillars.all.return_value = [
        MagicMock(id=f"p{i}", name=f"Pillar {i}", description=f"Desc {i}")
        for i in range(pillar_count)
    ]
    project.pxnodes.all.return_value = [
        MagicMock(id=f"n{i}", name=f"Node {i}", description=f"Desc {i}")
        for i in range(node_count)
    ]
    return project


PATCH_EXECUTE = (
    "pxnodes.llm.agents.consistency.semantic.pillar_alignment"
    ".PillarAlignmentAgent.execute"
)


class TestPillarAlignmentFindingParsing:
    def _workflow(self) -> ConsistencyWorkflow:
        return ConsistencyWorkflow(model_manager=MagicMock())

    def test_finding_parsed_into_consistency_finding(self):
        raw = [
            {
                "node_id": "n0",
                "pillar_id": "p0",
                "explanation": "Contradicts fun pillar",
                "confidence": 0.8,
            }
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert len(findings) == 1
        f = findings[0]
        assert f.category == "pillar_misalignment"
        assert f.severity == FindingSeverity.WARNING
        assert f.entity_id == "n0"
        assert "p0" in f.message
        assert "Contradicts fun pillar" in f.message
        assert "0.80" in f.message

    def test_multiple_findings_all_parsed(self):
        raw = [
            {
                "node_id": "n0",
                "pillar_id": "p0",
                "explanation": "Issue A",
                "confidence": 0.9,
            },
            {
                "node_id": "n1",
                "pillar_id": "p0",
                "explanation": "Issue B",
                "confidence": 0.6,
            },
        ]
        with patch(PATCH_EXECUTE, return_value=_make_result(raw)):
            findings, _, _ = self._workflow()._run_semantic_checks(
                _make_project(node_count=2)
            )

        assert len(findings) == 2

    def test_empty_findings_list_returns_no_findings(self):
        with patch(PATCH_EXECUTE, return_value=_make_result([])):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []

    def test_empty_pillars_skips_agent(self):
        project = _make_project()
        project.pillars.all.return_value = []

        with patch(PATCH_EXECUTE) as mock_exec:
            findings, _, _ = self._workflow()._run_semantic_checks(project)

        mock_exec.assert_not_called()
        assert findings == []

    def test_empty_nodes_skips_agent(self):
        project = _make_project()
        project.pxnodes.all.return_value = []

        with patch(PATCH_EXECUTE) as mock_exec:
            findings, _, _ = self._workflow()._run_semantic_checks(project)

        mock_exec.assert_not_called()
        assert findings == []

    def test_agent_failure_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_result([], success=False)):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []

    def test_agent_exception_returns_empty(self):
        with patch(PATCH_EXECUTE, side_effect=RuntimeError("LLM unavailable")):
            findings, _, _ = self._workflow()._run_semantic_checks(_make_project())

        assert findings == []

    def test_no_model_manager_skips_semantic_checks(self):
        workflow = ConsistencyWorkflow(model_manager=None)
        project = _make_project()

        with patch(PATCH_EXECUTE) as mock_exec:
            workflow._run_semantic_checks(project)

        mock_exec.assert_not_called()
