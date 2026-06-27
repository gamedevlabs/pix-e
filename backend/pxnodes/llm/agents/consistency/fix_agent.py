from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

from llm.agent_runtime import BaseAgent

# Shared JSON contract for every category. The model always returns the full
# (possibly unchanged) name + description, plus a list of the fields it actually
# changed with per-field reasoning, an overall summary, and the issue labels it
# resolved. This mirrors the node-validation fix shape so the frontend can show
# the same "AI Improvement Proposal" modal.
_RESPONSE_FORMAT = """
RESPONSE FORMAT (JSON):
{{
  "improved_name": "<the name — return it UNCHANGED unless fixing the name>",
  "improved_description": "<the description — UNCHANGED unless fixing it>",
  "changes": [
    {{
      "field": "name" or "description",
      "after": "<the new value of the field you changed>",
      "reasoning": "<one or two sentences: what you changed and why>",
      "issues_addressed": ["<short human label of the issue this change fixes>"]
    }}
  ],
  "overall_summary": "<one sentence summarizing the fix>",
  "issues_fixed": ["<short human label(s) of the issue(s) resolved>"]
}}

Only list a field in "changes" if you actually changed it.
"""

_PILLAR_MISALIGNMENT_PROMPT = """You are a game design assistant. A game design
node has been flagged because its description does not align with a core design
pillar.

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
Rewrite the node's DESCRIPTION so that it clearly and concretely supports the
design pillar above. Significant changes are expected and acceptable — do not
just add a token reference to the pillar.

Rules:
- The rewritten description must genuinely reflect the pillar's values and requirements
- Do NOT hedge or water down the pillar's direction
- Do NOT change the node name
- Write in the same style and approximate length as the original
{response_format}"""

_NODE_CONTRADICTION_PROMPT = """You are a game design assistant. Two game design
nodes have been flagged as contradicting each other.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

CONTRADICTION DETECTED:
{finding_description}

PROJECT DESIGN PILLARS (use these to decide which direction to commit to):
{pillars_section}
{other_nodes_section}
TASK:
Rewrite the DESCRIPTION of this node to fully resolve the contradiction.

Rules:
- Pick ONE clear interpretation that best supports the project pillars — do NOT
  blend or average the two contradicting descriptions
- The result must be internally consistent and no longer contradict the other node
- Do NOT change the node name
- Write in the same style and approximate length as the original
{response_format}"""

_TERMINOLOGY_PROMPT = """You are a game design assistant. A game design node uses
terminology that is inconsistent with the rest of the project.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

TERMINOLOGY ISSUE:
{finding_description}
{other_nodes_section}
TASK:
Rewrite the node's DESCRIPTION so it uses the project's established terminology
consistently.

Rules:
- Replace the inconsistent term(s) with the established project term — do not
  invent new names
- Change as little as possible beyond the terminology fix
- Do NOT change the node name
- Write in the same style and approximate length as the original
{response_format}"""

_EMPTY_DESCRIPTION_PROMPT = """You are a game design assistant. A game design
node is missing its description.

NODE TO FIX:
Name: {node_name}
Current Description: (empty)
{other_nodes_section}
TASK:
Write a clear, concise DESCRIPTION for this node that fits its name and is
consistent with the other nodes in the project.

Rules:
- The description must be concrete and match what the node name implies
- Use the project's established terminology
- Do NOT change the node name
{response_format}"""

_EMPTY_NAME_PROMPT = """You are a game design assistant. A game design node is
missing its NAME.

NODE TO FIX:
Name: (empty)
Current Description: {node_description}
{other_nodes_section}
TASK:
Propose a concise, descriptive NAME for this node based on its description.
Do NOT change the description.

Rules:
- The name must accurately summarize the description in a few words
- Use the project's established terminology and naming style
- Put the new name in "improved_name" and add a change with field "name"
- Return "improved_description" unchanged
{response_format}"""

_DUPLICATE_NAME_PROMPT = """You are a game design assistant. A game design node
shares its NAME with another node in the project, which is ambiguous.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}
{other_nodes_section}
TASK:
Propose a distinct, more specific NAME for this node so it is no longer a duplicate.
Do NOT change the description.

Rules:
- The new name must be unique within the project and clearly distinguish this
  node from the duplicate
- Keep it concise and consistent with the project's naming style
- Put the new name in "improved_name" and add a change with field "name"
- Return "improved_description" unchanged
{response_format}"""

_GENERIC_FIX_PROMPT = """You are a game design assistant. A consistency issue
has been detected in a game design node.

NODE TO FIX:
Name: {node_name}
Current Description: {node_description}

CONSISTENCY ISSUE ({finding_category}):
{finding_description}
{other_nodes_section}
TASK:
Rewrite the node's DESCRIPTION to resolve the identified issue.
Make only the changes necessary — do not introduce new inconsistencies.

Rules:
- Do NOT change the node name
- Write in the same style and approximate length as the original
{response_format}"""


class FieldChange(BaseModel):
    field: Literal["name", "description"]
    after: str
    reasoning: str
    issues_addressed: List[str] = Field(default_factory=list)


class ConsistencyFixResult(BaseModel):
    improved_name: str
    improved_description: str
    changes: List[FieldChange] = Field(default_factory=list)
    overall_summary: str = ""
    issues_fixed: List[str] = Field(default_factory=list)


class ConsistencyFixAgent(BaseAgent):
    """Suggests a corrected node for a consistency finding.

    Category-aware: structural name issues (empty_name, duplicate_node_name) are
    fixed on the NAME; everything else rewrites the DESCRIPTION. Returns a
    structured proposal (per-field changes + reasoning + summary) so the UI can
    render an explainable before/after.

    Note: ``orphaned_node`` is intentionally NOT handled here — a node not placed
    in any chart is a structural placement action, not a text fix; the API guards
    against it and the UI hides the button.
    """

    name = "consistency_fix"
    response_schema = ConsistencyFixResult

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
                response_format=_RESPONSE_FORMAT,
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
                response_format=_RESPONSE_FORMAT,
            )

        if category == "terminology_inconsistency":
            return _TERMINOLOGY_PROMPT.format(
                node_name=data["node_name"],
                node_description=data["node_description"],
                finding_description=data["finding_description"],
                other_nodes_section=other_nodes_section,
                response_format=_RESPONSE_FORMAT,
            )

        if category == "empty_description":
            return _EMPTY_DESCRIPTION_PROMPT.format(
                node_name=data["node_name"],
                other_nodes_section=other_nodes_section,
                response_format=_RESPONSE_FORMAT,
            )

        if category == "empty_name":
            return _EMPTY_NAME_PROMPT.format(
                node_description=data["node_description"],
                other_nodes_section=other_nodes_section,
                response_format=_RESPONSE_FORMAT,
            )

        if category == "duplicate_node_name":
            return _DUPLICATE_NAME_PROMPT.format(
                node_name=data["node_name"],
                node_description=data["node_description"],
                other_nodes_section=other_nodes_section,
                response_format=_RESPONSE_FORMAT,
            )

        return _GENERIC_FIX_PROMPT.format(
            node_name=data["node_name"],
            node_description=data["node_description"],
            finding_category=category,
            finding_description=data["finding_description"],
            other_nodes_section=other_nodes_section,
            response_format=_RESPONSE_FORMAT,
        )
