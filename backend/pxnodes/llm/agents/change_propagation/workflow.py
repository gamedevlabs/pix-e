import logging
from typing import List, Optional

from game_concept.models import Project
from llm.providers.manager import ModelManager
from pxnodes.models import PxNode

from .agent import ChangePropagationAgent
from .schemas import PropagationFinding, PropagationReport

logger = logging.getLogger(__name__)


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
    ) -> PropagationReport:
        if self._model_manager is None:
            raise ValueError(
                "ChangePropagationWorkflow requires a ModelManager — "
                "the Change Propagation Agent is entirely LLM-driven."
            )

        other_nodes: List[PxNode] = list(project.pxnodes.exclude(id=changed_node.id))

        agent = ChangePropagationAgent(
            model_manager=self._model_manager,
            min_confidence=min_confidence,
        )

        findings: List[PropagationFinding] = []
        try:
            findings = agent.analyze_change(
                changed_node=changed_node,
                old_description=old_description,
                new_description=new_description,
                other_nodes=other_nodes,
            )
        except Exception as e:
            logger.exception(
                "Semantic check '%s' failed: %s",
                agent.__class__.__name__,
                e,
            )

        return PropagationReport(
            changed_node_id=str(changed_node.id),
            findings=findings,
        )
