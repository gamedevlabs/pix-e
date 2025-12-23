"""
Atomic Fact extraction for PX Node descriptions.

LLM-based extraction following Zeng et al. (2024) methodology.
Extracts the smallest, indivisible units of information from narrative text.

Facts are cached in the vector store (memory_embeddings table) by the
StructuralMemoryGenerator. This module checks the vector store first
before generating new facts via LLM.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from pxnodes.llm.context.shared.prompts import (
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


def get_cached_facts_from_vector_store(
    node_id: str, chart_id: Optional[str] = None
) -> list[AtomicFact]:
    """
    Retrieve cached atomic facts from the vector store.

    Returns empty list if no cached facts found.
    """
    try:
        from pxnodes.llm.context.vector_store import VectorStore

        vector_store = VectorStore()
        memories = vector_store.get_memories_by_node(
            node_id=node_id,
            memory_type="atomic_fact",
            chart_id=chart_id,
        )
        vector_store.close()

        if memories:
            logger.debug(f"Found {len(memories)} cached facts for node {node_id}")
            return [
                AtomicFact(
                    node_id=node_id,
                    fact=m["content"],
                    source_field=m.get("metadata", {}).get(
                        "source_field", "description"
                    ),
                )
                for m in memories
            ]
    except Exception as e:
        logger.warning(f"Failed to retrieve cached facts from vector store: {e}")

    return []


def extract_atomic_facts(
    node: PxNode,
    llm_provider: Optional[LLMProvider] = None,
    model_id: Optional[str] = None,
    force_regenerate: bool = False,
    chart_id: Optional[str] = None,
) -> list[AtomicFact]:
    """
    Extract atomic facts from a PxNode's description and components.

    First checks the vector store for cached facts (stored by
    StructuralMemoryGenerator). Only calls LLM if:
    - No cached facts exist for this node in vector store
    - force_regenerate is True
    - llm_provider is provided

    Args:
        node: The PxNode to extract facts from
        llm_provider: LLM provider for generation (optional if using cache)
        model_id: Optional specific model to use
        force_regenerate: If True, skip cache and regenerate

    Returns:
        List of AtomicFact objects
    """
    node_id = str(node.id)

    # Check for cached facts in vector store first
    if not force_regenerate:
        cached_facts = get_cached_facts_from_vector_store(node_id, chart_id=chart_id)
        if cached_facts:
            logger.debug(f"Using {len(cached_facts)} cached facts for {node.name}")
            return cached_facts

    # No cached facts found - generate via LLM if provider available
    if not llm_provider:
        logger.debug(f"No cached facts and no LLM provider for {node.name}")
        return []

    logger.info(f"Generating atomic facts for {node.name} via LLM")
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

        logger.info(f"Generated {len(facts)} facts for {node.name}")

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


async def extract_atomic_facts_async(
    node: PxNode,
    llm_provider: LLMProvider,
    force_regenerate: bool = True,
    chart_id: Optional[str] = None,
) -> list[AtomicFact]:
    """
    Async version of extract_atomic_facts for parallel execution.

    Always uses force_regenerate=True to ensure fresh LLM-based extraction.
    Uses thread_sensitive=False for LLM calls to enable true parallelism.
    """
    import logfire
    from asgiref.sync import sync_to_async

    node_id = str(node.id)
    node_name = node.name

    with logfire.span(
        "extract_atomic_facts",
        node_id=node_id,
        node_name=node_name,
    ):
        # Check for cached facts in vector store first (if not force_regenerate)
        if not force_regenerate:
            cached_facts = await sync_to_async(
                get_cached_facts_from_vector_store, thread_sensitive=True
            )(node_id, chart_id)
            if cached_facts:
                logfire.info(
                    "atomic_facts_from_cache",
                    node_name=node_name,
                    fact_count=len(cached_facts),
                )
                return cached_facts

        # Generate via LLM
        logfire.info("generating_atomic_facts", node_name=node_name)

        # Get components (sync Django ORM call - must use thread_sensitive=True)
        components = await sync_to_async(
            get_node_components_for_prompt, thread_sensitive=True
        )(node)
        components_text = format_components_for_prompt(components)

        # Use description or fallback
        description = node.description or "No description provided."

        # Build the extraction prompt
        prompt = ATOMIC_FACT_EXTRACTION_PROMPT.format(
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
            parsed_facts = parse_atomic_facts(response)

            facts = [
                AtomicFact(
                    node_id=node_id,
                    fact=fact_text,
                    source_field="description",
                )
                for fact_text in parsed_facts
            ]

            logfire.info(
                "atomic_facts_generated",
                node_name=node_name,
                fact_count=len(facts),
            )
            return facts

        except Exception as e:
            logger.warning(f"Failed to extract atomic facts for {node_name}: {e}")
            logfire.error(
                "atomic_facts_failed",
                node_name=node_name,
                error=str(e),
            )
            return []
