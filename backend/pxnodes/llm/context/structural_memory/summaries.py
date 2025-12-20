"""
Summary extraction for PX Node content.

Summaries are LLM-generated condensed overviews of node content,
following Zeng et al. (2024) methodology.

Note: Summaries are generated on-demand via LLM. Unlike facts and triples,
they are not stored in the vector store by the StructuralMemoryGenerator.
Consider using fallback summaries for faster context building.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from pxnodes.models import PxNode

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class Summary:
    """Represents a condensed summary of a node."""

    node_id: str
    content: str
    source: str = "llm"  # 'llm' or 'fallback'

    def __str__(self) -> str:
        """String representation for context output."""
        return self.content


# Prompt for generating node summaries
SUMMARY_EXTRACTION_PROMPT = (
    "You are an intelligent assistant tasked with creating a concise summary "
    "of a game design node. Your summary should capture the essential "
    "information in 2-3 sentences.\n\n"
    "Focus on:\n"
    "- The main purpose or event of this node\n"
    "- Key gameplay elements (items, abilities, enemies)\n"
    "- Important narrative beats or story progression\n"
    "- The overall feel/intensity of this segment\n\n"
    "Keep the summary factual and concise. Do not add speculation.\n\n"
    "---\n\n"
    "Title: {title}\n"
    "Description: {description}\n"
    "Components:\n{components}\n\n"
    "Summary:"
)


def extract_summary(
    node: PxNode,
    llm_provider: Optional[LLMProvider] = None,
    model_id: Optional[str] = None,
) -> Summary:
    """
    Extract a condensed summary from a PxNode.

    Generates summary via LLM if provider available, otherwise uses fallback.
    Note: Unlike facts and triples, summaries are not cached in the vector store.

    Args:
        node: The PxNode to summarize
        llm_provider: LLM provider for generation (optional)
        model_id: Optional specific model to use

    Returns:
        Summary object
    """
    node_id = str(node.id)

    # If no LLM provider, use fallback
    if not llm_provider:
        return create_fallback_summary(node)

    logger.info(f"Generating summary for {node.name} via LLM")

    # Get components for context
    components = _get_node_components_for_prompt(node)
    components_text = _format_components(components)

    # Use description or fallback
    description = node.description or "No description provided."

    # Build the prompt
    prompt = SUMMARY_EXTRACTION_PROMPT.format(
        title=node.name,
        description=description,
        components=components_text,
    )

    # Generate using LLM
    try:
        response = llm_provider.generate(prompt)
        summary_text = _clean_summary(response)

        return Summary(node_id=node_id, content=summary_text, source="llm")
    except Exception as e:
        logger.warning(f"Failed to extract summary for node {node_id}: {e}")
        # Fallback to a simple summary
        return create_fallback_summary(node)


def create_fallback_summary(node: PxNode) -> Summary:
    """
    Create a simple fallback summary when LLM is unavailable.

    Uses the first sentence of the description or the node name.
    """
    node_id = str(node.id)

    if node.description:
        # Take first sentence or first 200 chars
        desc = node.description.strip()
        first_sentence = desc.split(".")[0] + "."
        if len(first_sentence) > 200:
            first_sentence = desc[:197] + "..."
        content = f"{node.name}: {first_sentence}"
    else:
        content = f"{node.name}: Game design node."

    return Summary(node_id=node_id, content=content, source="fallback")


def _clean_summary(response: str) -> str:
    """Clean up the LLM response to extract just the summary."""
    # Remove common prefixes
    response = response.strip()
    response = re.sub(r"^(Summary:?\s*)", "", response, flags=re.IGNORECASE)
    response = response.strip()

    # Limit to reasonable length
    if len(response) > 500:
        # Try to cut at sentence boundary
        sentences = response[:500].split(".")
        if len(sentences) > 1:
            response = ".".join(sentences[:-1]) + "."
        else:
            response = response[:497] + "..."

    return response


def _get_node_components_for_prompt(node: PxNode) -> list[dict[str, Any]]:
    """Get components from a node formatted for prompt inclusion."""
    components: list[dict[str, Any]] = []

    for comp in node.components.select_related("definition").all():
        components.append(
            {
                "definition_name": comp.definition.name,
                "definition_type": comp.definition.type,
                "value": comp.value,
            }
        )

    return components


def _format_components(components: list[dict[str, Any]]) -> str:
    """Format component list for inclusion in prompts."""
    if not components:
        return "- No components attached"

    lines = []
    for comp in components:
        name = comp.get("definition_name", "unknown")
        comp_type = comp.get("definition_type", "")
        value = comp.get("value", "N/A")
        if comp_type:
            lines.append(f"- {name} ({comp_type}): {value}")
        else:
            lines.append(f"- {name}: {value}")

    return "\n".join(lines)


def extract_summaries_batch(
    nodes: list[PxNode],
    llm_provider: LLMProvider,
    model_id: Optional[str] = None,
) -> dict[str, Summary]:
    """
    Extract summaries from multiple nodes.

    Returns a dictionary mapping node_id to Summary.
    """
    results: dict[str, Summary] = {}

    for node in nodes:
        node_id = str(node.id)
        summary = extract_summary(node, llm_provider, model_id)
        results[node_id] = summary

    return results


async def extract_summary_async(
    node: PxNode,
    llm_provider: LLMProvider,
) -> Summary:
    """
    Async version of extract_summary for parallel execution.

    Uses thread_sensitive=False for LLM calls to enable true parallelism.
    """
    import logfire
    from asgiref.sync import sync_to_async

    node_id = str(node.id)
    node_name = node.name

    with logfire.span(
        "extract_summary",
        node_id=node_id,
        node_name=node_name,
    ):
        logfire.info("generating_summary", node_name=node_name)

        # Get components (sync Django ORM call - must use thread_sensitive=True)
        components = await sync_to_async(
            _get_node_components_for_prompt, thread_sensitive=True
        )(node)
        components_text = _format_components(components)

        # Use description or fallback
        description = node.description or "No description provided."

        # Build the prompt
        prompt = SUMMARY_EXTRACTION_PROMPT.format(
            title=node_name,
            description=description,
            components=components_text,
        )

        # Generate using LLM - use thread_sensitive=False for true parallelism
        # LLM calls are HTTP requests, not Django ORM, so safe to parallelize
        try:
            response = await sync_to_async(
                llm_provider.generate, thread_sensitive=False
            )(prompt)
            summary_text = _clean_summary(response)

            logfire.info(
                "summary_generated",
                node_name=node_name,
                summary_length=len(summary_text),
            )
            return Summary(node_id=node_id, content=summary_text, source="llm")

        except Exception as e:
            logger.warning(f"Failed to extract summary for {node_name}: {e}")
            logfire.error(
                "summary_failed",
                node_name=node_name,
                error=str(e),
            )
            # Return fallback summary
            return create_fallback_summary(node)
