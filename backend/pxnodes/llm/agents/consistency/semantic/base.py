from typing import Any, Dict

from llm.agent_runtime import BaseAgent
from pxnodes.llm.agents.consistency.schemas import FindingSeverity


class SemanticConsistencyAgent(BaseAgent):
    """
    Subclasses must define:
    - name: Agent identifier
    - category: Consistency finding category string
    - response_schema: Pydantic model for the LLM response
    - prompt_template: Prompt string with format placeholders
    - build_prompt(data): Formats prompt_template with data
    """

    category: str = ""
    default_severity: FindingSeverity = FindingSeverity.WARNING
    prompt_template: str = ""

    def __init__(self) -> None:
        if not self.category:
            raise ValueError(
                f"{self.__class__.__name__} must define 'category' class attribute"
            )
        if not self.prompt_template:
            raise ValueError(
                f"{self.__class__.__name__} must define "
                "'prompt_template' class attribute"
            )
        super().__init__()

    def build_prompt(self, data: Dict[str, Any]) -> str:
        raise NotImplementedError
