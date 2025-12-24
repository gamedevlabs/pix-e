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
    - Path Robustness: Does node work across incoming/outgoing paths?
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

        # Get dimension-specific context
        dimension_context = self._build_dimension_context(data)

        target_block = target_node_name
        if target_node_description:
            target_block = f"{target_node_name}\nDescription: {target_node_description}"

        return self.prompt_template.format(
            context=context_string,
            target_node_name=target_block,
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

COHERENCE_CONTEXT_HEADER = """You are a game design coherence analyzer evaluating a node in a game flow chart.  # noqa: E501

CONTEXT:
{context}

TARGET NODE: {target_node_name}

{dimension_context}
"""
