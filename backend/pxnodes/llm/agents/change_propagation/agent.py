import logging
from typing import Any, Dict, List

from pydantic import BaseModel

from llm.agent_runtime import BaseAgent
from llm.providers.manager import ModelManager

from .schemas import PropagationFinding

logger = logging.getLogger(__name__)

CHANGE_PROPAGATION_PROMPT = """You are a game design document analyzer.

A PxNode in the game design graph has been updated. Your task is to identify
which other nodes in the project are semantically affected by this change and
may need to be updated.

CHANGED NODE:
- Name: {changed_node_name}
- Old Description: {old_description}
- New Description: {new_description}

OTHER NODES IN THE PROJECT:
{other_nodes_section}

TASK:
For each node that is meaningfully affected by this change, report a finding.
When evaluating affected nodes, check TWO directions:

1. ADDITIONS: Does the new description introduce new concepts, mechanics, or
   features that other nodes should reflect? For example: a renamed mechanic,
   a new dependency, a contradiction with what another node states.

2. REMOVALS: Does the old description contain concepts, mechanics, or features
   that are now absent from the new description? If so, check whether any
   other nodes still reference those removed concepts — if they do, those
   nodes need updating to remove or replace those references.

Both directions can produce affected nodes. Do not ignore removals.

Do NOT report:
- Nodes that merely share a theme but are not directly impacted
- Vague or speculative connections

RESPONSE FORMAT (JSON):
{{
  "findings": [
    {{
      "affected_node_id": "<uuid of the affected node>",
      "affected_node_name": "<name of the affected node>",
      "reason": "Clear explanation of why this node is affected by the change",
      "confidence": <float between 0.0 and 1.0>,
      "suggested_action": "Concrete suggestion for how to update this node"
    }}
  ]
}}
"""


class ChangePropagationResponse(BaseModel):
    """LLM response schema for the change propagation agent."""

    findings: List[PropagationFinding]


class ChangePropagationAgent(BaseAgent):
    """Given a changed PxNode and its old/new description, finds other PxNodes
    in the same project that are semantically affected by the change."""

    name = "change_propagation"
    response_schema = ChangePropagationResponse
    prompt_template = CHANGE_PROPAGATION_PROMPT

    def __init__(
        self,
        model_manager: ModelManager,
        min_confidence: float = 0.5,
    ) -> None:
        self._model_manager = model_manager
        self._min_confidence = min_confidence
        super().__init__()

    def build_prompt(self, data: Dict[str, Any]) -> str:
        other_nodes_section = "\n".join(
            f"- ID: {n['id']}, Name: {n['name']}\n"
            f"  Description: {n.get('description', '')}"
            for n in data.get("other_nodes", [])
        )
        return self.prompt_template.format(
            changed_node_name=data["changed_node_name"],
            old_description=data["old_description"],
            new_description=data["new_description"],
            other_nodes_section=other_nodes_section,
        )

    def analyze_change(
        self,
        changed_node: Any,
        old_description: str,
        new_description: str,
        other_nodes: list,
    ) -> List[PropagationFinding]:
        if not other_nodes:
            return []

        data: Dict[str, Any] = {
            "changed_node_name": changed_node.name,
            "old_description": old_description,
            "new_description": new_description,
            "other_nodes": [
                {
                    "id": str(n.id),
                    "name": n.name,
                    "description": n.description,
                }
                for n in other_nodes
            ],
        }
        context = {"model_manager": self._model_manager, "data": data}
        result = self.execute(context)

        if not result.success or not result.data:
            if not result.success:
                logger.warning(
                    "ChangePropagationAgent failed for node '%s': %s",
                    changed_node.name,
                    result.error.message if result.error else "unknown error",
                )
            return []

        findings = []
        for item in result.data.get("findings", []):
            if item.get("confidence", 0.0) < self._min_confidence:
                continue
            findings.append(
                PropagationFinding(
                    affected_node_id=item["affected_node_id"],
                    affected_node_name=item["affected_node_name"],
                    reason=item["reason"],
                    confidence=item["confidence"],
                    suggested_action=item["suggested_action"],
                )
            )
        return findings
