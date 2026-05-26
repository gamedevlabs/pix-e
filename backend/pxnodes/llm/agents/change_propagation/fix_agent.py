from typing import Any, Dict

from pydantic import BaseModel

from llm.agent_runtime import BaseAgent
from llm.providers.manager import ModelManager

_PROPAGATION_FIX_PROMPT = """You are a game design consistency assistant.

A game design node was just updated. A related node is now potentially out of sync and needs to be rewritten to stay consistent with the change.

CHANGED NODE: {changed_node_name}
OLD DESCRIPTION: {changed_node_old_description}
NEW DESCRIPTION: {changed_node_new_description}

AFFECTED NODE: {affected_node_name}
CURRENT DESCRIPTION: {affected_node_current_description}

TASK: Rewrite the description of '{affected_node_name}' so that it is consistent with the updated '{changed_node_name}'. Keep the core purpose and scope of '{affected_node_name}' intact — only adjust what is necessary to reflect the change. Do not introduce new mechanics or features.

RESPONSE FORMAT (JSON):
{{
  "suggested_description": "The rewritten description"
}}
"""


class PropagationFixResponse(BaseModel):
    suggested_description: str


class ChangePropagationFixAgent(BaseAgent):
    """Suggests a corrected description for a node affected by a change to another node."""

    name = "change_propagation_fix"
    response_schema = PropagationFixResponse

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return _PROPAGATION_FIX_PROMPT.format(
            changed_node_name=data["changed_node_name"],
            changed_node_old_description=data["changed_node_old_description"],
            changed_node_new_description=data["changed_node_new_description"],
            affected_node_name=data["affected_node_name"],
            affected_node_current_description=data["affected_node_current_description"],
        )

    def fix(self, data: dict) -> str:
        context = {"model_manager": ModelManager(), "data": data}
        result = self.execute(context)
        if not result.success and result.error:
            if "rate limit" in (result.error.message or "").lower():
                raise Exception("rate limit reached. Please wait and try again.")
        if not result.success or not result.data:
            msg = result.error.message if result.error else "Fix generation failed"
            raise Exception(msg)
        return result.data["suggested_description"]
