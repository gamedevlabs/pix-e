from typing import Any, Dict

from pydantic import BaseModel

from llm.agent_runtime import BaseAgent

_PILLAR_MISALIGNMENT_PROMPT = """You are a game design assistant. A game design node has been flagged because its description does not align with a core design pillar.

DESIGN PILLAR:
Name: {pillar_name}
Description: {pillar_description}

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

FINDING:
{finding_description}
{other_nodes_section}
TASK:
Rewrite the node's description so that it clearly and concretely supports the design pillar above.
Significant changes are expected and acceptable — do not just add a token reference to the pillar.

Rules:
- The rewritten description must genuinely reflect the pillar's values and requirements
- Do NOT hedge or water down the pillar's direction
- Do NOT change the node name
- Write in the same style and approximate length as the original

RESPONSE FORMAT (JSON):
{{
  "suggested_description": "The rewritten description"
}}
"""

_NODE_CONTRADICTION_PROMPT = """You are a game design assistant. Two game design nodes have been flagged as contradicting each other.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

CONTRADICTION DETECTED:
{finding_description}

PROJECT DESIGN PILLARS (use these to decide which direction to commit to):
{pillars_section}
{other_nodes_section}
TASK:
Rewrite the description of this node to fully resolve the contradiction.

Rules:
- Pick ONE clear interpretation that best supports the project pillars — do NOT blend or average the two contradicting descriptions
- The result must be internally consistent and no longer contradict the other node
- Do NOT change the node name
- Write in the same style and approximate length as the original

RESPONSE FORMAT (JSON):
{{
  "suggested_description": "The rewritten description"
}}
"""

_GENERIC_FIX_PROMPT = """You are a game design assistant. A consistency issue has been detected in a game design node.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

CONSISTENCY ISSUE ({finding_category}):
{finding_description}
{other_nodes_section}
TASK:
Rewrite the node's description to resolve the identified issue.
Make only the changes necessary — do not introduce new inconsistencies.

Rules:
- Do NOT change the node name
- Write in the same style and approximate length as the original

RESPONSE FORMAT (JSON):
{{
  "suggested_description": "The rewritten description"
}}
"""


class FixDescriptionResponse(BaseModel):
    suggested_description: str


class ConsistencyFixAgent(BaseAgent):
    """Suggests a corrected description for a node with a consistency finding.

    Uses category-specific prompts:
    - pillar_misalignment: rewrites to genuinely align with the pillar
    - node_contradiction: picks one interpretation, does not merge
    - other: generic minimal fix
    """

    name = "consistency_fix"
    response_schema = FixDescriptionResponse

    def _build_other_nodes_section(self, data: Dict[str, Any]) -> str:
        other_nodes = data.get("other_nodes", [])
        if not other_nodes:
            return ""
        lines = ["OTHER NODES IN THIS PROJECT (for terminology reference only):"]
        for n in other_nodes:
            lines.append(f"- {n['name']}: {n['description']}")
        lines.append(
            "\nIMPORTANT: Use the same terminology as the other nodes above. "
            "Do not introduce new terms for concepts that already have established "
            "names in this project."
        )
        return "\n" + "\n".join(lines) + "\n"

    def build_prompt(self, data: Dict[str, Any]) -> str:
        category = data.get("finding_category", "")
        other_nodes_section = self._build_other_nodes_section(data)

        if category == "pillar_misalignment":
            return _PILLAR_MISALIGNMENT_PROMPT.format(
                pillar_name=data.get("pillar_name", "Unknown pillar"),
                pillar_description=data.get(
                    "pillar_description", "No description available."
                ),
                node_name=data["node_name"],
                node_description=data["node_description"],
                finding_description=data["finding_description"],
                other_nodes_section=other_nodes_section,
            )

        if category == "node_contradiction":
            return _NODE_CONTRADICTION_PROMPT.format(
                node_name=data["node_name"],
                node_description=data["node_description"],
                finding_description=data["finding_description"],
                pillars_section=data.get(
                    "pillars_section", "No design pillars defined."
                ),
                other_nodes_section=other_nodes_section,
            )

        return _GENERIC_FIX_PROMPT.format(
            node_name=data["node_name"],
            node_description=data["node_description"],
            finding_category=category,
            finding_description=data["finding_description"],
            other_nodes_section=other_nodes_section,
        )
