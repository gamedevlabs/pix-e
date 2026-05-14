from typing import Any, Dict, List

from pydantic import BaseModel, Field

from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.semantic.base import SemanticConsistencyAgent

TERMINOLOGY_CONSISTENCY_PROMPT = """You are a game design terminology analyzer.

You are given a list of game nodes, each with an ID, name, and description.
Your task is to find cases where two or more nodes use different terms for
what appears to be the same game concept.

GAME NODES:
{nodes_section}

TASK:
Identify pairs of nodes that use different terminology for what appears to be
the same underlying game concept. For example, one node may refer to a
"stamina bar" while another describes an "energy meter" for the same mechanic.

Only flag cases where the terms are genuinely interchangeable — meaning they
refer to the same game concept and could reasonably be unified under one term.
Do NOT flag:
- Terms that describe genuinely different concepts (e.g. "health" vs "stamina")
- Stylistic variations that are intentional (e.g. in-universe lore terminology)
- Cases where context makes clear the concepts are distinct

The confidence score should reflect how certain you are that both terms refer
to the same underlying concept. If no terminology conflicts exist, return an
empty conflicts list.

RESPONSE FORMAT (JSON):
{{
  "conflicts": [
    {{
      "node_a_id": "<uuid of first node>",
      "node_a_name": "<name of first node>",
      "term_a": "<term used in first node>",
      "node_b_id": "<uuid of second node>",
      "node_b_name": "<name of second node>",
      "term_b": "<term used in second node>",
      "message": "Clear description of why these terms appear to refer to the same concept",
      "confidence": <float between 0.0 and 1.0>
    }}
  ]
}}
"""


class TerminologyConflictItem(BaseModel):
    """A pair of nodes that use different terms for the same game concept."""

    node_a_id: str
    node_a_name: str
    term_a: str
    node_b_id: str
    node_b_name: str
    term_b: str
    message: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class TerminologyConsistencyResponse(BaseModel):
    """Full response from the TerminologyConsistencyAgent."""

    conflicts: List[TerminologyConflictItem]


class TerminologyConsistencyAgent(SemanticConsistencyAgent):
    """Detects pairs of nodes that use different terms for the same game concept."""

    name = "terminology_consistency"
    category = "terminology_inconsistency"
    default_severity = FindingSeverity.INFO
    response_schema = TerminologyConsistencyResponse
    prompt_template = TERMINOLOGY_CONSISTENCY_PROMPT

    def build_prompt(self, data: Dict[str, Any]) -> str:
        nodes = data.get("nodes", [])
        nodes_section = "\n".join(
            f"- ID: {n['id']}, Name: {n['name']}\n"
            f"  Description: {n.get('description', '')}"
            for n in nodes
        )
        return self.prompt_template.format(nodes_section=nodes_section)
