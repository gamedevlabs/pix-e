from typing import Any, Dict, List

from pydantic import BaseModel, Field

from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.semantic.base import SemanticConsistencyAgent

TERMINOLOGY_CONSISTENCY_PROMPT = """You are a game design terminology analyzer.

You are given a list of game nodes, each with an ID, name, and description.
Your task is to find cases where two or more nodes use conflicting terms that
represent genuinely different design decisions for the same aspect of the game —
conflicts that would cause confusion or contradiction if both nodes were
implemented as described.

GAME NODES:
{nodes_section}

TASK:
Identify pairs of nodes where the SAME underlying concept, mechanic, or system
is referred to using different names or terms across nodes — regardless of
whether the descriptions are otherwise logically compatible. This category is
distinct from NODE_CONTRADICTION: you are not looking for mutually exclusive
design decisions, but for naming inconsistencies that could cause confusion
during development or documentation.

DO flag cases like:
- One node calls it a "stamina bar", another calls it an "energy meter" for
  what is clearly the same resource mechanic
- One node says "experience points", another says "skill points" for the same
  progression currency
- One node uses "biome", another uses "zone" or "region" to mean the same
  structural concept

Do NOT flag synonyms or paraphrases of the same concept as terminology
inconsistencies. Only flag terms where using them interchangeably would cause
a genuine design contradiction or player confusion. Concretely, do NOT flag:
- Near-synonyms that describe the same idea at different granularities (e.g.
  "paths" vs "terrain", "zones" vs "areas", "maneuvers" vs "movement",
  "ground-level terrain" vs "ground-level paths")
- Stylistic or lore-specific naming that is clearly intentional
- Related but distinct sub-concepts that coexist naturally (e.g. "health" and
  "stamina" are different resources, not conflicting terms)
- Cases where context makes clear the concepts are distinct and compatible
- Mutually exclusive design decisions — those belong in NODE_CONTRADICTION

The confidence score should reflect how certain you are that both terms refer
to the exact same underlying mechanic or concept. If no terminology
inconsistencies exist, return an empty conflicts list.

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
      "message": "Clear description of why these terms appear to refer"
      " to the same concept",
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
