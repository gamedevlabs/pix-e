"""
Document Context Agent for SPARC V2.

Extracts aspect-relevant content from uploaded design documents.
"""

from typing import Any, Dict

from sparc.llm.agents.v2.base import V2BaseAgent
from sparc.llm.prompts.v2.document_context import (
    DOCUMENT_CONTEXT_SYSTEM_PROMPT,
    build_document_context_prompt,
)
from sparc.llm.schemas.v2.document_context import DocumentContextResponse
from sparc.llm.utils.file_extraction import extract_text_from_file


class DocumentContextAgent(V2BaseAgent):
    """
    Agent that extracts aspect-relevant content from design documents.

    Similar to RouterAgent but operates on uploaded documents instead of
    user-provided game text. Runs in parallel with Router and Pillar Context
    in Stage 1 of SPARC V2 evaluation.
    """

    name = "document_context"
    response_schema = DocumentContextResponse
    aspect_name = "document_context"
    temperature = 0

    def validate_input(self, data: Dict[str, Any]) -> None:
        """Validate that required inputs are provided."""
        if not data.get("file_path"):
            raise ValueError("file_path is required")
        if not data.get("target_aspects"):
            raise ValueError("target_aspects is required")

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """Build the document context prompt."""
        import os

        file_path = data["file_path"]
        target_aspects = data["target_aspects"]

        if not os.path.exists(file_path):
            raise ValueError(
                f"Document file not found at {file_path}. "
                f"File may have been deleted before processing."
            )

        try:
            document_text = extract_text_from_file(file_path)
        except ValueError as e:
            raise ValueError(f"Failed to extract document text: {str(e)}")

        max_chars = 50000 * 4
        if len(document_text) > max_chars:
            document_text = document_text[:max_chars]

        base_prompt = build_document_context_prompt(target_aspects)

        return f"""{DOCUMENT_CONTEXT_SYSTEM_PROMPT}

{base_prompt}

## DESIGN DOCUMENT

{document_text}
"""
