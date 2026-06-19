import logging
from typing import Any, Dict, List, Optional

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

GRAPH_AWARE_PROPAGATION_PROMPT = """You are a game design document analyzer.

A PxNode in the game design graph has been updated. Your task is to identify
which other nodes are semantically affected by this change and may need to be
updated.

CHANGED NODE:
- Name: {changed_node_name}
- Old Description: {old_description}
- New Description: {new_description}

RELATED NODES (with their structural relationship to the changed node):
{other_nodes_section}

Relationship labels:
- PREDECESSOR: this node comes BEFORE the changed node in the dependency graph
  (the changed node builds on what this node establishes)
- SUCCESSOR: this node comes AFTER the changed node
  (it depends on or extends what the changed node provides)
- SAME_CHART: this node is in the same chart but not directly connected

TASK:
For each node that is meaningfully affected by this change, report a finding.
Check TWO directions:

1. ADDITIONS: Does the new description introduce new concepts, mechanics, or
   features? SUCCESSOR nodes are most likely to need updating — they build on
   the changed node. Also check PREDECESSOR nodes for contradictions.

2. REMOVALS: Does the old description contain concepts now absent from the new
   description? Check whether SUCCESSOR or SAME_CHART nodes still reference
   those removed concepts — if so, they need updating.

Prioritise PREDECESSOR and SUCCESSOR nodes. Only report SAME_CHART nodes if
the evidence of impact is strong.

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

ITERATIVE_PROPAGATION_PROMPT = """You are a game design document analyzer.

A change is propagating transitively through a game design graph.

ORIGINAL CHANGE:
- Changed Node: {changed_node_name}
- Old Description: {old_description}
- New Description: {new_description}

TRANSITIVELY AFFECTED NODE (the node we are now expanding from):
- Name: {affected_node_name}
- Current Description: {affected_node_description}
- Why this node was affected: {reason_chain}

NEIGHBORS OF "{affected_node_name}":
{neighbors_section}

Relationship labels (relative to {affected_node_name}):
- PREDECESSOR: this node comes BEFORE {affected_node_name} in the dependency graph
- SUCCESSOR: this node comes AFTER {affected_node_name} (depends on or extends it)

TASK:
Determine whether the original change propagates further through {affected_node_name}
to any of its listed neighbors. A neighbor is affected only if there is a clear,
concrete semantic connection — not just because it is nearby in the graph.

Do NOT report:
- Nodes that merely share a theme but are not directly impacted
- Vague or speculative connections

RESPONSE FORMAT (JSON):
{{
  "findings": [
    {{
      "affected_node_id": "<uuid>",
      "affected_node_name": "<name>",
      "reason": "Clear explanation of why this node is transitively affected",
      "confidence": <float between 0.0 and 1.0>,
      "suggested_action": "Concrete suggestion for how to update this node"
    }}
  ]
}}
"""


PAIRWISE_PROPAGATION_PROMPT = """You are a game design document analyzer.

A PxNode in the game design graph has been updated. You must decide whether ONE
specific other node is DIRECTLY affected by this change and needs updating.

CHANGED NODE:
- Name: {changed_node_name}
- Old Description: {old_description}
- New Description: {new_description}

CANDIDATE NODE (decide about THIS node only):
- ID: {candidate_id}
- Name: {candidate_name}
- Description: {candidate_description}

TASK:
Decide whether the CANDIDATE node is affected by the change and needs an update.
Check both directions: concepts the change ADDED/renamed that the candidate
should now reflect, and concepts the change REMOVED that the candidate still
references.

Apply a HIGH bar. In a real project the vast majority of nodes are NOT affected
by any single change. Report the candidate as affected ONLY if there is a
concrete, direct dependency — it references a specific mechanic, feature, value,
or entity that the change added, removed, renamed, or contradicted. Do NOT report
the candidate merely because it shares a theme, domain, genre, or general topic
with the changed node.

If the candidate is not clearly and directly affected, return an empty findings
list. Returning no finding is the correct answer for most candidates.

RESPONSE FORMAT (JSON) — contains 0 or 1 finding:
{{
  "findings": [
    {{
      "affected_node_id": "{candidate_id}",
      "affected_node_name": "{candidate_name}",
      "reason": "Concrete explanation of the direct dependency",
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
        model_id: Optional[str] = None,
    ) -> None:
        self._model_manager = model_manager
        self._min_confidence = min_confidence
        self._model_id = model_id
        super().__init__()

    def build_prompt(self, data: Dict[str, Any]) -> str:
        # Allow callers to bypass template building with a pre-built prompt.
        if "_raw_prompt" in data:
            return data["_raw_prompt"]

        use_graph = data.get("use_graph_context", False)
        nodes = data.get("other_nodes", [])

        if use_graph:
            other_nodes_section = "\n".join(
                f"- [{n.get('relationship', 'UNKNOWN')}] ID: {n['id']}, Name: {n['name']}\n"
                f"  Description: {n.get('description', '')}"
                for n in nodes
            )
            template = GRAPH_AWARE_PROPAGATION_PROMPT
        else:
            other_nodes_section = "\n".join(
                f"- ID: {n['id']}, Name: {n['name']}\n"
                f"  Description: {n.get('description', '')}"
                for n in nodes
            )
            template = CHANGE_PROPAGATION_PROMPT

        return template.format(
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
        use_graph_context: bool = False,
    ) -> List[PropagationFinding]:
        if not other_nodes:
            return []

        formatted: List[Dict[str, Any]] = []
        for n in other_nodes:
            if isinstance(n, dict):
                formatted.append(n)
            else:
                formatted.append({
                    "id": str(n.id),
                    "name": n.name,
                    "description": n.description or "",
                    "relationship": None,
                })

        data: Dict[str, Any] = {
            "changed_node_name": changed_node.name,
            "old_description": old_description,
            "new_description": new_description,
            "use_graph_context": use_graph_context,
            "other_nodes": formatted,
        }
        context = {
            "model_manager": self._model_manager,
            "data": data,
            "model_id": self._model_id,
        }
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

    def analyze_pair(
        self,
        changed_node: Any,
        old_description: str,
        new_description: str,
        candidate: Any,
    ) -> List[PropagationFinding]:
        """Pointwise judgement over a SINGLE candidate node.

        Uses a dedicated strict binary prompt (high bar, "most nodes are NOT
        affected") rather than reusing the listwise flat prompt with one item —
        the latter triggers a strong yes-bias because it is framed as "report all
        affected nodes". Returns 0 or 1 finding for this candidate.
        """
        if isinstance(candidate, dict):
            cid = str(candidate["id"])
            cname = candidate["name"]
            cdesc = candidate.get("description", "") or ""
        else:
            cid = str(candidate.id)
            cname = candidate.name
            cdesc = candidate.description or ""

        prompt = PAIRWISE_PROPAGATION_PROMPT.format(
            changed_node_name=changed_node.name,
            old_description=old_description,
            new_description=new_description,
            candidate_id=cid,
            candidate_name=cname,
            candidate_description=cdesc,
        )

        context = {
            "model_manager": self._model_manager,
            "data": {"_raw_prompt": prompt},
            "model_id": self._model_id,
        }
        result = self.execute(context)

        if not result.success or not result.data:
            if not result.success:
                logger.warning(
                    "ChangePropagationAgent (pairwise) failed for candidate '%s': %s",
                    cname,
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

    def analyze_transitive_change(
        self,
        changed_node_name: str,
        old_description: str,
        new_description: str,
        affected_node_name: str,
        affected_node_description: str,
        reason_chain: str,
        neighbors: List[Dict[str, Any]],
    ) -> List[PropagationFinding]:
        """Ask the LLM whether a change propagates further from an already-affected
        node to its direct neighbors."""
        if not neighbors:
            return []

        neighbors_section = "\n".join(
            f"- [{n.get('relationship', 'UNKNOWN')}] ID: {n['id']}, Name: {n['name']}\n"
            f"  Description: {n.get('description', '')}"
            for n in neighbors
        )

        prompt = ITERATIVE_PROPAGATION_PROMPT.format(
            changed_node_name=changed_node_name,
            old_description=old_description,
            new_description=new_description,
            affected_node_name=affected_node_name,
            affected_node_description=affected_node_description,
            reason_chain=reason_chain,
            neighbors_section=neighbors_section,
        )

        data: Dict[str, Any] = {"_raw_prompt": prompt}
        context = {
            "model_manager": self._model_manager,
            "data": data,
            "model_id": self._model_id,
        }
        result = self.execute(context)

        if not result.success or not result.data:
            if not result.success:
                logger.warning(
                    "ChangePropagationAgent (transitive) failed for node '%s': %s",
                    affected_node_name,
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
