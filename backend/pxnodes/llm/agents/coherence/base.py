"""
Base class for coherence dimension agents.

Extends BaseAgent with PxNodes-specific functionality:
- Integration with context strategies
- DB persistence for evaluation results
- Standardized prompt templates
"""

from abc import abstractmethod
from typing import Any, Dict, Type

from pydantic import BaseModel

from llm.agent_runtime import BaseAgent
from pxnodes.llm.agents.coherence.schemas import CoherenceDimensionResult


class CoherenceDimensionAgent(BaseAgent):
    """
    Base class for coherence dimension evaluation agents.

    Each dimension agent evaluates one aspect of node coherence:
    - Backward Coherence: Does node respect what came before?
    - Forward Coherence: Does node properly set up future?
    - Global Fit: Does node align with concept and pillars?
    - Node Integrity: Do title/description/components align?

    Subclasses must define:
    - name: Agent identifier
    - dimension_name: Human-readable dimension name
    - response_schema: Pydantic model for response
    - prompt_template: LLM prompt template
    """

    # Subclasses must define these
    dimension_name: str = ""
    prompt_template: str = ""
    response_schema: Type[BaseModel] = CoherenceDimensionResult

    # Agent settings
    temperature: float = 0

    def __init__(self) -> None:
        """Initialize the agent."""
        if not self.dimension_name:
            raise ValueError(
                f"{self.__class__.__name__} must define 'dimension_name' attribute"
            )
        if not self.prompt_template:
            raise ValueError(
                f"{self.__class__.__name__} must define 'prompt_template' attribute"
            )
        super().__init__()

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the evaluation prompt from context data.

        Args:
            data: Must contain:
                - context_string: Formatted context from strategy
                - target_node_name: Name of the node being evaluated
                - Additional dimension-specific data

        Returns:
            Formatted prompt string
        """
        context_string = data.get("context_string", "No context provided")
        target_node_name = data.get("target_node_name", "Unknown")
        target_node_description = data.get("target_node_description")
        node_details = data.get("node_details", {})
        target_facts = data.get("target_node_facts", [])
        target_triples = data.get("target_node_triples", [])
        target_summary = data.get("target_node_summary")
        target_chunks = data.get("target_node_chunks", [])

        # Get dimension-specific context
        dimension_context = self._build_dimension_context(data)

        target_block_lines = [f"Title: {target_node_name}"]
        if target_node_description:
            target_block_lines.append(f"Description: {target_node_description}")
        components = node_details.get("components", [])
        if components:
            target_block_lines.append("Components:")
            for comp in components[:10]:
                if isinstance(comp, dict):
                    name = comp.get("name", "Component")
                    value = comp.get("value", "")
                    target_block_lines.append(f"- {name}: {value}")
        if target_summary:
            target_block_lines.append("Summary:")
            target_block_lines.append(f"- {target_summary}")
        if target_facts:
            target_block_lines.append("Atomic Facts:")
            for fact in target_facts[:10]:
                target_block_lines.append(f"- {fact}")
        if target_triples:
            target_block_lines.append("Knowledge Triples:")
            for triple in target_triples[:10]:
                target_block_lines.append(f"- {triple}")
        if target_chunks:
            target_block_lines.append("Chunks:")
            for chunk in target_chunks[:4]:
                target_block_lines.append(f"- {chunk}")
        target_block = "\n".join(target_block_lines)

        return self.prompt_template.format(
            context=context_string,
            target_node_block=target_block,
            dimension_context=dimension_context,
        )

    @abstractmethod
    def _build_dimension_context(self, data: Dict[str, Any]) -> str:
        """
        Build dimension-specific context section.

        Override in subclasses to add dimension-specific information.

        Args:
            data: Full input data dictionary

        Returns:
            Dimension-specific context string to inject into prompt
        """
        pass

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate that required context is provided."""
        if not data.get("context_string"):
            raise ValueError("context_string is required for coherence evaluation")


# Common prompt parts that can be reused
SCORING_INSTRUCTIONS = """
SCORING SCALE (1-6):
1 - Very Poor: Major issues that break coherence
2 - Poor: Significant issues that harm coherence
3 - Below Average: Notable issues that need attention
4 - Above Average: Minor issues, generally coherent
5 - Good: Very few issues, well-designed
6 - Excellent: No issues, exemplary coherence

RESPONSE FORMAT:
{{
  "score": <1-6>,
  "reasoning": "Detailed explanation of your score",
  "issues": ["Issue 1", "Issue 2", ...],
  "suggestions": ["Suggestion 1", "Suggestion 2", ...],
  "evidence": ["Short references to nodes/edges/quotes"],
  "unknowns": ["What could not be verified from context"],
  "path_variance": "consistent across paths OR depends on path: <details>"
}}
"""

COHERENCE_CONTEXT_HEADER = """You are a game design coherence analyzer \
evaluating a node in a game flow chart.

EVIDENCE RULES (general):
- Only use information explicitly stated in the CONTEXT below. Do NOT assume \
missing mechanics, items, or events.
- Evidence must be a direct quote (or near-direct paraphrase) from the \
CONTEXT.
- If you cite a node title, include a quoted fragment from that node's \
description that supports the claim.

TARGET NODE DETAILS:
{target_node_block}

CONTEXT:
{context}

{dimension_context}
"""
