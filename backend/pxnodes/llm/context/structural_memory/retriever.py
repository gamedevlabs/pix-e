"""
Iterative Memory Retriever for Structural Memory.

Implements the iterative retrieval method from Zeng et al. (2024)
"On the Structural Memory of LLM Agents".

The retriever refines queries over N iterations to improve retrieval
accuracy for coherence evaluation tasks.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

import logfire

from pxnodes.llm.context.shared.embeddings import OpenAIEmbeddingGenerator
from pxnodes.llm.context.shared.vector_store import VectorStore

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM provider interface."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text from prompt."""
        ...


@dataclass
class RetrievedMemory:
    """A memory retrieved from the vector store."""

    id: str
    node_id: str
    chart_id: Optional[str]
    memory_type: str  # "knowledge_triple" or "atomic_fact"
    content: str
    metadata: Optional[dict[str, Any]]
    distance: float  # Similarity distance (lower = more similar)

    def __str__(self) -> str:
        if self.memory_type == "knowledge_triple":
            return f"Triple: {self.content}"
        return f"Fact: {self.content}"


@dataclass
class RetrievalResult:
    """Result of memory retrieval."""

    query: str
    refined_queries: list[str] = field(default_factory=list)
    memories: list[RetrievedMemory] = field(default_factory=list)
    iterations_performed: int = 0

    def get_triples(self) -> list[RetrievedMemory]:
        """Get only knowledge triple memories."""
        return [m for m in self.memories if m.memory_type == "knowledge_triple"]

    def get_facts(self) -> list[RetrievedMemory]:
        """Get only atomic fact memories."""
        return [m for m in self.memories if m.memory_type == "atomic_fact"]

    def format_for_prompt(self) -> str:
        """Format retrieved memories for LLM prompt."""
        lines = []

        triples = self.get_triples()
        if triples:
            lines.append("[KNOWLEDGE TRIPLES]")
            for t in triples:
                lines.append(f"- {t.content}")

        facts = self.get_facts()
        if facts:
            lines.append("\n[ATOMIC FACTS]")
            for f in facts:
                lines.append(f"- {f.content}")

        return "\n".join(lines)


# Query refinement prompt from Zeng et al.
QUERY_REFINEMENT_PROMPT = """You are helping to refine a search query \
for better memory retrieval.

Original Query: {original_query}

Retrieved Memories (may be incomplete or noisy):
{retrieved_memories}

Based on what was retrieved, refine the query to better capture the needed information.
Focus on:
1. Key entities (items, abilities, characters) mentioned
2. Relationships between nodes
3. Specific game mechanics or events

Return ONLY the refined query, nothing else."""


class IterativeRetriever:
    """
    Implements iterative retrieval from Zeng et al. (2024).

    The retriever:
    1. Performs initial retrieval with the query
    2. Uses LLM to refine the query based on retrieved memories
    3. Repeats for N iterations
    4. Returns accumulated unique memories

    This approach helps surface relevant information that might be missed
    by a single retrieval pass.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize the retriever.

        Args:
            llm_provider: LLM for query refinement
            embedding_model: OpenAI embedding model for query embedding
        """
        self.llm_provider = llm_provider
        self.embedding_generator = OpenAIEmbeddingGenerator(model=embedding_model)
        self.vector_store = VectorStore()

    def retrieve(
        self,
        query: str,
        node_ids: Optional[list[str]] = None,
        memory_type: Optional[str] = None,
        iterations: int = 3,
        top_k: int = 10,
    ) -> RetrievalResult:
        """
        Perform iterative retrieval.

        Args:
            query: Initial query for retrieval
            node_ids: Optional list of node IDs to filter by
            memory_type: Optional filter ("knowledge_triple" or "atomic_fact")
            iterations: Number of refinement iterations
            top_k: Number of memories to retrieve per iteration

        Returns:
            RetrievalResult with all retrieved memories
        """
        with logfire.span(
            "retrieval.iterative.structural_memory",
            query=query,
            iterations=iterations,
            top_k=top_k,
        ):
            result = RetrievalResult(query=query)
            seen_ids: set[str] = set()
            current_query = query

            for i in range(iterations):
                with logfire.span(
                    "retrieval.iteration.structural_memory",
                    iteration=i + 1,
                    query=current_query,
                ):
                    # Retrieve memories for current query
                    new_memories = self._retrieve_single(
                        current_query,
                        node_ids=node_ids,
                        memory_type=memory_type,
                        limit=top_k,
                    )

                    # Add only unseen memories
                    for memory in new_memories:
                        if memory.id not in seen_ids:
                            seen_ids.add(memory.id)
                            result.memories.append(memory)

                    result.iterations_performed = i + 1

                    logfire.info(
                        "retrieval.iteration.complete.structural_memory",
                        iteration=i + 1,
                        new_memories=len(new_memories),
                        total_memories=len(result.memories),
                    )

                    # Refine query for next iteration (except last)
                    if i < iterations - 1 and new_memories:
                        refined = self._refine_query(current_query, new_memories)
                        if refined and refined != current_query:
                            result.refined_queries.append(refined)
                            current_query = refined
                            logfire.info(
                                "retrieval.query_refined.structural_memory",
                                iteration=i + 1,
                                refined_query=refined[:100],
                            )

            logfire.info(
                "retrieval.complete.structural_memory",
                total_memories=len(result.memories),
                iterations=result.iterations_performed,
                refined_queries=len(result.refined_queries),
            )

            return result

    def retrieve_for_nodes(
        self,
        target_node_id: str,
        neighbor_node_ids: list[str],
        query: str,
        iterations: int = 3,
        top_k_per_node: int = 5,
    ) -> dict[str, RetrievalResult]:
        """
        Retrieve memories for a target node and its neighbors.

        Returns a dict mapping node_id to RetrievalResult.
        Useful for building evaluation context.
        """
        results: dict[str, RetrievalResult] = {}

        # Retrieve for target node
        results[target_node_id] = self.retrieve(
            query=query,
            node_ids=[target_node_id],
            iterations=iterations,
            top_k=top_k_per_node,
        )

        # Retrieve for each neighbor
        for neighbor_id in neighbor_node_ids:
            # Adapt query for neighbor context
            neighbor_query = f"Context for node connected to: {query}"
            results[neighbor_id] = self.retrieve(
                query=neighbor_query,
                node_ids=[neighbor_id],
                iterations=max(1, iterations - 1),  # Fewer iterations for neighbors
                top_k=top_k_per_node,
            )

        return results

    def _retrieve_single(
        self,
        query: str,
        node_ids: Optional[list[str]] = None,
        memory_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[RetrievedMemory]:
        """Perform a single retrieval pass."""
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)

        # Search vector store
        raw_results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            limit=limit,
            memory_type=memory_type,
            node_ids=node_ids,
        )

        # Convert to RetrievedMemory objects
        memories = []
        for r in raw_results:
            memories.append(
                RetrievedMemory(
                    id=r["id"],
                    node_id=r["node_id"],
                    chart_id=r.get("chart_id"),
                    memory_type=r["memory_type"],
                    content=r["content"],
                    metadata=r.get("metadata"),
                    distance=r.get("distance", 0.0),
                )
            )

        return memories

    def _refine_query(
        self,
        original_query: str,
        retrieved_memories: list[RetrievedMemory],
    ) -> Optional[str]:
        """Use LLM to refine the query based on retrieved memories."""
        # Format memories for prompt
        memory_text = "\n".join(
            f"- [{m.memory_type}] {m.content}" for m in retrieved_memories[:10]
        )

        prompt = QUERY_REFINEMENT_PROMPT.format(
            original_query=original_query,
            retrieved_memories=memory_text,
        )

        try:
            refined = self.llm_provider.generate(prompt, operation="retrieval_refine")
            # Clean up response
            refined = refined.strip().strip('"').strip("'")
            return refined if refined else None
        except Exception as e:
            logger.warning(f"Failed to refine query: {e}")
            return None

    def close(self) -> None:
        """Close resources."""
        self.vector_store.close()


def format_memories_by_node(
    memories_by_node: dict[str, RetrievalResult],
    node_names: dict[str, str],
) -> str:
    """
    Format memories from multiple nodes into a structured context string.

    Args:
        memories_by_node: Dict mapping node_id to RetrievalResult
        node_names: Dict mapping node_id to human-readable name

    Returns:
        Formatted context string for LLM prompt
    """
    sections = []

    for node_id, result in memories_by_node.items():
        node_name = node_names.get(node_id, node_id)
        section = f"[NODE: {node_name}]\n{result.format_for_prompt()}"
        sections.append(section)

    return "\n\n".join(sections)
