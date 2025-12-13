"""
Atomic Fact extraction for PX Node descriptions.

LLM-based extraction following Zeng et al. (2024) methodology.
Extracts the smallest, indivisible units of information from narrative text.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from pxnodes.llm.context.prompts import (
    ATOMIC_FACT_EXTRACTION_PROMPT,
    format_components_for_prompt,
)
from pxnodes.models import PxNode

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class AtomicFact:
    """Represents an atomic fact extracted from a node description."""

    node_id: str
    fact: str
    source_field: str = "description"  # 'description', 'title', or 'components'

    def __str__(self) -> str:
        """String representation for context output."""
        return self.fact


def parse_atomic_facts(response: str) -> list[str]:
    """
    Parse atomic facts from LLM response.

    Expected format:
    1. Fact one.
    2. Fact two.
    ...
    """
    facts: list[str] = []

    # Split by newlines and filter
    lines = response.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove numbering patterns: "1.", "1)", "- ", "* "
        cleaned = re.sub(r"^[\d]+[.)\-]\s*", "", line)
        cleaned = re.sub(r"^[-*]\s*", "", cleaned)
        cleaned = cleaned.strip()

        if cleaned and len(cleaned) > 5:  # Minimum meaningful length
            facts.append(cleaned)

    return facts


def get_node_components_for_prompt(node: PxNode) -> list[dict[str, Any]]:
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


def extract_atomic_facts(
    node: PxNode,
    llm_provider: LLMProvider,
    model_id: Optional[str] = None,
) -> list[AtomicFact]:
    """
    Extract atomic facts from a PxNode's description and components using LLM.

    This is the lazy extraction approach - called on-demand during evaluation.
    Now includes component data in the extraction prompt.

    Args:
        node: The PxNode to extract facts from
        llm_provider: LLM provider for generation
        model_id: Optional specific model to use

    Returns:
        List of AtomicFact objects
    """
    node_id = str(node.id)
    facts: list[AtomicFact] = []

    # Get components
    components = get_node_components_for_prompt(node)
    components_text = format_components_for_prompt(components)

    # Use description or fallback to empty
    description = node.description or "No description provided."

    # Build the extraction prompt with components
    prompt = ATOMIC_FACT_EXTRACTION_PROMPT.format(
        title=node.name,
        description=description,
        components=components_text,
    )

    # Generate using LLM
    try:
        response = llm_provider.generate(prompt)
        parsed_facts = parse_atomic_facts(response)

        for fact_text in parsed_facts:
            facts.append(
                AtomicFact(
                    node_id=node_id,
                    fact=fact_text,
                    source_field="description",
                )
            )
    except Exception as e:
        logger.warning(f"Failed to extract atomic facts for node {node_id}: {e}")

    return facts


def extract_atomic_facts_batch(
    nodes: list[PxNode],
    llm_provider: LLMProvider,
    model_id: Optional[str] = None,
) -> dict[str, list[AtomicFact]]:
    """
    Extract atomic facts from multiple nodes.

    Returns a dictionary mapping node_id to list of facts.
    """
    results: dict[str, list[AtomicFact]] = {}

    for node in nodes:
        node_id = str(node.id)
        facts = extract_atomic_facts(node, llm_provider, model_id)
        results[node_id] = facts

    return results


def create_title_fact(node: PxNode) -> AtomicFact:
    """
    Create a simple fact from the node title.

    This is a deterministic fallback when LLM extraction isn't available.
    """
    return AtomicFact(
        node_id=str(node.id),
        fact=f'This node is titled "{node.name}".',
        source_field="title",
    )
