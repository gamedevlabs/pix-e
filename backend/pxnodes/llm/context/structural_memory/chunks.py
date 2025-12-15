"""
Chunk extraction for PX Node content.

Chunks represent raw text segments from node descriptions and components,
following Zeng et al. (2024) methodology.
"""

from dataclasses import dataclass
from typing import Any

from pxnodes.models import PxNode


@dataclass
class Chunk:
    """Represents a raw text chunk from a node."""

    node_id: str
    content: str
    source: str = "description"  # 'description', 'component', 'name'

    def __str__(self) -> str:
        """String representation for context output."""
        return self.content


def extract_chunks(node: PxNode, max_chunk_size: int = 500) -> list[Chunk]:
    """
    Extract raw text chunks from a PxNode.

    Chunks are the raw text segments without any transformation,
    preserving the original content for tasks requiring full context.

    Args:
        node: The PxNode to extract chunks from
        max_chunk_size: Maximum characters per chunk (splits if exceeded)

    Returns:
        List of Chunk objects
    """
    node_id = str(node.id)
    chunks: list[Chunk] = []

    # Chunk from name
    if node.name:
        chunks.append(
            Chunk(node_id=node_id, content=f"Node: {node.name}", source="name")
        )

    # Chunk from description
    if node.description:
        desc = node.description.strip()
        if len(desc) <= max_chunk_size:
            chunks.append(Chunk(node_id=node_id, content=desc, source="description"))
        else:
            # Split long descriptions into chunks
            for i in range(0, len(desc), max_chunk_size):
                chunk_text = desc[i : i + max_chunk_size]
                chunks.append(
                    Chunk(node_id=node_id, content=chunk_text, source="description")
                )

    # Chunks from components
    for comp in node.components.select_related("definition").all():
        comp_text = _format_component(comp)
        if comp_text:
            chunks.append(Chunk(node_id=node_id, content=comp_text, source="component"))

    return chunks


def _format_component(comp: Any) -> str:
    """Format a component as a chunk string."""
    definition = comp.definition
    value = comp.value

    if not value:
        return ""

    # Format based on type
    if isinstance(value, dict):
        if "text" in value:
            return f"{definition.name}: {value['text']}"
        return f"{definition.name}: {value}"
    elif isinstance(value, list):
        items = ", ".join(str(v) for v in value[:5])
        return f"{definition.name}: [{items}]"
    else:
        return f"{definition.name}: {value}"


def extract_chunks_batch(
    nodes: list[PxNode],
    max_chunk_size: int = 500,
) -> dict[str, list[Chunk]]:
    """
    Extract chunks from multiple nodes.

    Returns a dictionary mapping node_id to list of chunks.
    """
    results: dict[str, list[Chunk]] = {}

    for node in nodes:
        node_id = str(node.id)
        chunks = extract_chunks(node, max_chunk_size)
        results[node_id] = chunks

    return results
