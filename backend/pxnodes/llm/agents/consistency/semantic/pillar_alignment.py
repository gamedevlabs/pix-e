from typing import Any, Dict, List

from pydantic import BaseModel, Field

from pxnodes.llm.agents.consistency.schemas import FindingSeverity
from pxnodes.llm.agents.consistency.semantic.base import SemanticConsistencyAgent

PILLAR_ALIGNMENT_PROMPT = """You are a game design consistency analyzer.

You are given a list of design pillars and a list of game nodes. Your task is
to identify nodes that thematically contradict or violate one or more design
pillars.

DESIGN PILLARS:
{pillars_section}

GAME NODES:
{nodes_section}

TASK:
For each node that clearly contradicts a pillar, report a finding. Only report
findings where you are reasonably confident (confidence >= 0.5). If no
contradictions exist, return an empty findings list.

RESPONSE FORMAT (JSON):
{{
  "findings": [
    {{
      "node_id": "<uuid of the contradicting node>",
      "pillar_id": "<uuid of the violated pillar>",
      "explanation": "Clear explanation of how the node contradicts the pillar",
      "confidence": <float between 0.0 and 1.0>
    }}
  ]
}}
"""


class PillarFindingItem(BaseModel):
    """A single node-pillar contradiction detected by the LLM."""

    node_id: str
    pillar_id: str
    explanation: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class PillarAlignmentResponse(BaseModel):
    """Full response from the PillarAlignmentAgent."""

    findings: List[PillarFindingItem]


class PillarAlignmentAgent(SemanticConsistencyAgent):
    """Detects nodes that thematically contradict a design pillar."""

    name = "pillar_alignment"
    category = "pillar_misalignment"
    default_severity = FindingSeverity.WARNING
    response_schema = PillarAlignmentResponse
    prompt_template = PILLAR_ALIGNMENT_PROMPT

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return self.prompt_template.format(
            pillars_section=data.get("pillars_section", ""),
            nodes_section=data.get("nodes_section", ""),
        )
