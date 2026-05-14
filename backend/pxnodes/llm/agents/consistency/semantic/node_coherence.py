from typing import Any, Dict, List

from pydantic import BaseModel, Field

from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.semantic.base import SemanticConsistencyAgent

NODE_COHERENCE_PROMPT = """You are a game design consistency analyzer.

You are given a list of game nodes, each with an ID, name, and description.
Your task is to find pairs of nodes whose descriptions directly contradict
each other in a logical sense.

GAME NODES:
{nodes_section}

TASK:
Identify pairs of nodes that contain genuine logical contradictions — for
example, one node describes "turn-based combat" while another describes
"real-time combat". Do NOT report:
- Stylistic differences (e.g. tone or art style variations)
- Missing information (e.g. one node lacks detail the other has)
- Thematic tension that is intentional (e.g. "hope" vs "despair" as themes)

Only report contradictions where two nodes explicitly state incompatible facts.
If no contradictions exist, return an empty contradictions list.

RESPONSE FORMAT (JSON):
{{
  "contradictions": [
    {{
      "node_a_id": "<uuid of first node>",
      "node_a_name": "<name of first node>",
      "node_b_id": "<uuid of second node>",
      "node_b_name": "<name of second node>",
      "message": "Clear description of the contradiction",
      "confidence": <float between 0.0 and 1.0>
    }}
  ]
}}
"""


class NodeContradictionItem(BaseModel):
    """A pair of nodes whose descriptions logically contradict each other."""

    node_a_id: str
    node_a_name: str
    node_b_id: str
    node_b_name: str
    message: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class NodeCoherenceResponse(BaseModel):
    """Full response from the NodeCoherenceAgent."""

    contradictions: List[NodeContradictionItem]


class NodeCoherenceAgent(SemanticConsistencyAgent):
    """Detects pairs of nodes whose descriptions logically contradict each other."""

    name = "node_coherence"
    category = "node_contradiction"
    default_severity = FindingSeverity.WARNING
    response_schema = NodeCoherenceResponse
    prompt_template = NODE_COHERENCE_PROMPT

    def build_prompt(self, data: Dict[str, Any]) -> str:
        nodes = data.get("nodes", [])
        nodes_section = "\n".join(
            f"- ID: {n['id']}, Name: {n['name']}\n  Description: {n['description']}"
            for n in nodes
        )
        return self.prompt_template.format(nodes_section=nodes_section)
