from unittest.mock import MagicMock, patch

import pytest

from llm.types import AgentResult
from pxnodes.llm.agents.change_propagation.agent import ChangePropagationAgent
from pxnodes.llm.agents.change_propagation.schemas import PropagationFinding
from pxnodes.llm.agents.change_propagation.workflow import ChangePropagationWorkflow

PATCH_EXECUTE = (
    "pxnodes.llm.agents.change_propagation.agent.ChangePropagationAgent.execute"
)
PATCH_ANALYZE = (
    "pxnodes.llm.agents.change_propagation.workflow"
    ".ChangePropagationAgent.analyze_change"
)


def _make_agent_result(findings_data: list, success: bool = True) -> AgentResult:
    return AgentResult(
        agent_name="change_propagation",
        success=success,
        data={"findings": findings_data} if success else None,
        execution_time_ms=0,
    )


def _finding_dict(
    node_id: str = "n1",
    node_name: str = "Node 1",
    reason: str = "Test reason",
    confidence: float = 0.8,
    suggested_action: str = "Update this node",
) -> dict:
    return {
        "affected_node_id": node_id,
        "affected_node_name": node_name,
        "reason": reason,
        "confidence": confidence,
        "suggested_action": suggested_action,
    }


def _make_node(
    node_id: str = "node-1",
    name: str = "Node 1",
    description: str = "A description",
) -> MagicMock:
    node = MagicMock()
    node.id = node_id
    node.name = name
    node.description = description
    return node


def _make_project(other_nodes: list) -> MagicMock:
    project = MagicMock()
    project.pxnodes.exclude.return_value = other_nodes
    return project


def _make_propagation_finding(**kwargs) -> PropagationFinding:
    defaults = dict(
        affected_node_id="n1",
        affected_node_name="Node 1",
        reason="Referenced mechanic was renamed",
        confidence=0.9,
        suggested_action="Update the mechanic reference",
    )
    return PropagationFinding(**{**defaults, **kwargs})


class TestChangePropagationAgent:
    def _agent(self, min_confidence: float = 0.5) -> ChangePropagationAgent:
        return ChangePropagationAgent(
            model_manager=MagicMock(),
            min_confidence=min_confidence,
        )

    def test_empty_other_nodes_returns_empty_without_llm_call(self):
        with patch(PATCH_EXECUTE) as mock_exec:
            result = self._agent().analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[],
            )

        mock_exec.assert_not_called()
        assert result == []

    def test_finding_above_threshold_is_returned(self):
        raw = [_finding_dict(confidence=0.8)]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent(min_confidence=0.5).analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("n1")],
            )

        assert len(result) == 1
        assert isinstance(result[0], PropagationFinding)

    def test_finding_below_threshold_is_filtered(self):
        raw = [_finding_dict(confidence=0.3)]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent(min_confidence=0.5).analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("n1")],
            )

        assert result == []

    def test_mixed_confidence_only_above_threshold_returned(self):
        raw = [
            _finding_dict(node_id="n1", confidence=0.9),
            _finding_dict(node_id="n2", confidence=0.2),
            _finding_dict(node_id="n3", confidence=0.6),
        ]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent(min_confidence=0.5).analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node(f"n{i}") for i in range(3)],
            )

        assert len(result) == 2
        assert result[0].affected_node_id == "n1"
        assert result[1].affected_node_id == "n3"

    def test_fields_mapped_correctly_to_propagation_finding(self):
        raw = [
            _finding_dict(
                node_id="abc-123",
                node_name="Combat Node",
                reason="Mechanic was renamed",
                confidence=0.9,
                suggested_action="Update references to use new name",
            )
        ]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent().analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("abc-123")],
            )

        assert len(result) == 1
        f = result[0]
        assert f.affected_node_id == "abc-123"
        assert f.affected_node_name == "Combat Node"
        assert f.reason == "Mechanic was renamed"
        assert f.confidence == 0.9
        assert f.suggested_action == "Update references to use new name"

    def test_multiple_findings_all_returned(self):
        raw = [
            _finding_dict(node_id="n1", confidence=0.9),
            _finding_dict(node_id="n2", confidence=0.7),
            _finding_dict(node_id="n3", confidence=0.8),
        ]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent(min_confidence=0.5).analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node(f"n{i}") for i in range(3)],
            )

        assert len(result) == 3

    def test_llm_failure_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_agent_result([], success=False)):
            result = self._agent().analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("n1")],
            )

        assert result == []

    def test_empty_llm_findings_returns_empty(self):
        with patch(PATCH_EXECUTE, return_value=_make_agent_result([])):
            result = self._agent().analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("n1")],
            )

        assert result == []

    def test_finding_at_exact_threshold_is_returned(self):
        raw = [_finding_dict(confidence=0.5)]
        with patch(PATCH_EXECUTE, return_value=_make_agent_result(raw)):
            result = self._agent(min_confidence=0.5).analyze_change(
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                other_nodes=[_make_node("n1")],
            )

        assert len(result) == 1


class TestChangePropagationWorkflow:
    def _workflow(self) -> ChangePropagationWorkflow:
        return ChangePropagationWorkflow(model_manager=MagicMock())

    def test_raises_when_no_model_manager(self):
        workflow = ChangePropagationWorkflow(model_manager=None)

        with pytest.raises(ValueError, match="ModelManager"):
            workflow.check_change(
                project=_make_project([]),
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
            )

    def test_report_contains_correct_changed_node_id(self):
        changed_node = _make_node(node_id="node-xyz")

        with patch(PATCH_ANALYZE, return_value=[]):
            report = self._workflow().check_change(
                project=_make_project([]),
                changed_node=changed_node,
                old_description="old",
                new_description="new",
            )

        assert report.changed_node_id == "node-xyz"

    def test_excludes_changed_node_from_db_query(self):
        changed_node = _make_node(node_id="changed-1")
        project = _make_project([])

        with patch(PATCH_ANALYZE, return_value=[]):
            self._workflow().check_change(
                project=project,
                changed_node=changed_node,
                old_description="old",
                new_description="new",
            )

        project.pxnodes.exclude.assert_called_once_with(id="changed-1")

    def test_other_nodes_passed_to_agent(self):
        changed_node = _make_node(node_id="changed-1")
        other = [_make_node("n1"), _make_node("n2")]
        project = _make_project(other_nodes=other)

        with patch(PATCH_ANALYZE, return_value=[]) as mock_analyze:
            self._workflow().check_change(
                project=project,
                changed_node=changed_node,
                old_description="old",
                new_description="new",
            )

        assert mock_analyze.call_args.kwargs["other_nodes"] == other

    def test_descriptions_passed_to_agent(self):
        project = _make_project([_make_node("n1")])

        with patch(PATCH_ANALYZE, return_value=[]) as mock_analyze:
            self._workflow().check_change(
                project=project,
                changed_node=_make_node(),
                old_description="the old text",
                new_description="the new text",
            )

        kwargs = mock_analyze.call_args.kwargs
        assert kwargs["old_description"] == "the old text"
        assert kwargs["new_description"] == "the new text"

    def test_empty_project_returns_empty_findings(self):
        with patch(PATCH_ANALYZE, return_value=[]):
            report = self._workflow().check_change(
                project=_make_project(other_nodes=[]),
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
            )

        assert report.findings == []

    def test_agent_findings_flow_into_report(self):
        findings = [
            _make_propagation_finding(affected_node_id="n1"),
            _make_propagation_finding(affected_node_id="n2"),
        ]
        project = _make_project([_make_node("n1"), _make_node("n2")])

        with patch(PATCH_ANALYZE, return_value=findings):
            report = self._workflow().check_change(
                project=project,
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
            )

        assert len(report.findings) == 2
        assert report.findings[0].affected_node_id == "n1"
        assert report.findings[1].affected_node_id == "n2"

    def test_min_confidence_forwarded_to_agent(self):
        project = _make_project([_make_node("n1")])
        workflow = self._workflow()

        with patch(
            "pxnodes.llm.agents.change_propagation.workflow.ChangePropagationAgent"
        ) as MockAgent:
            MockAgent.return_value.analyze_change.return_value = []
            workflow.check_change(
                project=project,
                changed_node=_make_node(),
                old_description="old",
                new_description="new",
                min_confidence=0.75,
            )

        assert MockAgent.call_args.kwargs["min_confidence"] == 0.75
