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
Identify pairs of nodes where the game design logic or intended player
experience is MUTUALLY EXCLUSIVE — i.e. both cannot be true at the same time
in a working game. The contradiction must be about design intent or game
mechanics, not about wording or naming.

DO flag:
- "turn-based combat" vs "real-time combat" (mutually exclusive systems)
- "single player only" vs "co-op multiplayer" (incompatible player count)
- "permanent death, no saves" vs "checkpoint-based respawn" (contradictory
  death mechanics)

Do NOT flag:
- Nodes that agree on the underlying concept but use different names for it
  (e.g. "stamina bar" vs "energy meter" for the same resource — that is a
  TERMINOLOGY_INCONSISTENCY, not a contradiction). If the only difference
  between two nodes is the name or label used for the same mechanic, do not
  flag it as a contradiction.
- Stylistic differences, tone, or art direction variations
- Missing information (one node lacks detail the other has)
- Thematic tension that is intentional (e.g. "hope" vs "despair" as themes)

Only flag contradictions where two nodes explicitly state incompatible design
decisions. If no such contradictions exist, return an empty contradictions
list.

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
