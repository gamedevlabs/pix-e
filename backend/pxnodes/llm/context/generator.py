"""
Structural Memory Generator with Change Detection.

Orchestrates the generation of knowledge triples, atomic facts, and embeddings
for PX nodes in a chart, with intelligent change detection to skip unchanged
nodes.

Supports batch processing of up to 10 nodes at a time for efficient embedding
generation.
"""

import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

import logfire

from pxcharts.models import PxChart
from pxnodes.llm.context.change_detection import (
    get_changed_nodes,
    update_processing_state,
)
from pxnodes.llm.context.embeddings import OpenAIEmbeddingGenerator
from pxnodes.llm.context.facts import extract_atomic_facts
from pxnodes.llm.context.graph_retrieval import get_graph_slice
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
from pxnodes.llm.context.triples import (
    compute_derived_triples,
    extract_all_triples,
)
from pxnodes.llm.context.vector_store import VectorStore
from pxnodes.models import PxNode

logger = logging.getLogger(__name__)

# Maximum nodes to process in a single batch
BATCH_SIZE = 10


@dataclass
class NodeProcessingResult:
    """Result of processing a single node."""

    node_id: str
    node_name: str
    triples_count: int = 0
    facts_count: int = 0
    embeddings_count: int = 0
    skipped: bool = False
    error: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of generating structural memory for a chart."""

    chart_id: str
    chart_name: str
    processed_nodes: list[NodeProcessingResult] = field(default_factory=list)
    skipped_nodes: list[NodeProcessingResult] = field(default_factory=list)
    total_triples: int = 0
    total_facts: int = 0
    total_embeddings: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def processed_count(self) -> int:
        return len(self.processed_nodes)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_nodes)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "chart_id": self.chart_id,
            "chart_name": self.chart_name,
            "processed": self.processed_count,
            "skipped": self.skipped_count,
            "total_triples": self.total_triples,
            "total_facts": self.total_facts,
            "total_embeddings": self.total_embeddings,
            "processed_nodes": [
                {
                    "node_id": n.node_id,
                    "node_name": n.node_name,
                    "triples": n.triples_count,
                    "facts": n.facts_count,
                    "embeddings": n.embeddings_count,
                }
                for n in self.processed_nodes
            ],
            "skipped_nodes": [
                {"node_id": n.node_id, "node_name": n.node_name}
                for n in self.skipped_nodes
            ],
            "errors": self.errors,
        }


class StructuralMemoryGenerator:
    """
    Generates structural memory (triples, facts, embeddings) for charts.

    Features:
    - Change detection to skip unchanged nodes
    - Real LLM for atomic fact extraction
    - OpenAI embeddings for vector storage
    - Logfire integration for tracking
    """

    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        skip_embeddings: bool = False,
        force_regenerate: bool = False,
    ):
        """
        Initialize the generator.

        Args:
            llm_model: Model for atomic fact extraction
            embedding_model: OpenAI embedding model
            skip_embeddings: If True, skip embedding generation
            force_regenerate: If True, process all nodes regardless of changes
        """
        self.llm_provider = LLMProviderAdapter(
            model_name=llm_model,
            temperature=0.3,
        )
        self.embedding_generator: Optional[OpenAIEmbeddingGenerator] = None
        if not skip_embeddings:
            self.embedding_generator = OpenAIEmbeddingGenerator(model=embedding_model)

        self.skip_embeddings = skip_embeddings
        self.force_regenerate = force_regenerate
        self.vector_store = VectorStore()

    def generate_for_chart(self, chart: PxChart) -> GenerationResult:
        """
        Generate structural memory for all changed nodes in a chart.

        Processes nodes in batches of up to BATCH_SIZE (10) for efficiency.
        Uses parallel processing for fact extraction and batch embedding generation.

        Args:
            chart: The chart to process

        Returns:
            GenerationResult with statistics and details
        """
        with logfire.span(
            "structural_memory.generate_for_chart",
            chart_id=str(chart.id),
            chart_name=chart.name,
        ):
            result = GenerationResult(
                chart_id=str(chart.id),
                chart_name=chart.name,
            )

            # Get changed and unchanged nodes
            if self.force_regenerate:
                # Get all nodes in chart
                containers = chart.containers.filter(
                    content__isnull=False
                ).select_related("content")
                changed_nodes: list[PxNode] = [
                    c.content for c in containers if c.content is not None
                ]
                unchanged_nodes: list[PxNode] = []
            else:
                changed_nodes, unchanged_nodes = get_changed_nodes(chart)

            # Record skipped nodes
            for node in unchanged_nodes:
                result.skipped_nodes.append(
                    NodeProcessingResult(
                        node_id=str(node.id),
                        node_name=node.name,
                        skipped=True,
                    )
                )

            logfire.info(
                "structural_memory.nodes_to_process",
                changed=len(changed_nodes),
                unchanged=len(unchanged_nodes),
                force=self.force_regenerate,
                batch_size=BATCH_SIZE,
            )

            # Process changed nodes in batches
            for i in range(0, len(changed_nodes), BATCH_SIZE):
                batch = changed_nodes[i : i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(changed_nodes) + BATCH_SIZE - 1) // BATCH_SIZE

                logfire.info(
                    "structural_memory.processing_batch",
                    batch_num=batch_num,
                    total_batches=total_batches,
                    batch_size=len(batch),
                )

                try:
                    batch_results = self._process_batch(batch, chart)
                    for node_result in batch_results:
                        if node_result.error:
                            result.errors.append(
                                f"Node {node_result.node_name}: {node_result.error}"
                            )
                        result.processed_nodes.append(node_result)
                        result.total_triples += node_result.triples_count
                        result.total_facts += node_result.facts_count
                        result.total_embeddings += node_result.embeddings_count
                except Exception as e:
                    logger.error(f"Error processing batch {batch_num}: {e}")
                    logfire.error(
                        "structural_memory.batch_processing_failed",
                        batch_num=batch_num,
                        error=str(e),
                    )
                    # Record errors for all nodes in failed batch
                    for node in batch:
                        result.errors.append(f"Node {node.name}: {str(e)}")
                        result.processed_nodes.append(
                            NodeProcessingResult(
                                node_id=str(node.id),
                                node_name=node.name,
                                error=str(e),
                            )
                        )

            logfire.info(
                "structural_memory.generation_complete",
                chart_id=str(chart.id),
                processed=result.processed_count,
                skipped=result.skipped_count,
                total_triples=result.total_triples,
                total_facts=result.total_facts,
                total_embeddings=result.total_embeddings,
            )

            return result

    def _process_batch(
        self, nodes: list[PxNode], chart: PxChart
    ) -> list[NodeProcessingResult]:
        """
        Process a batch of nodes in parallel.

        Steps:
        1. Extract triples for all nodes (deterministic, fast)
        2. Extract facts for all nodes in parallel (LLM calls)
        3. Batch generate embeddings for all texts
        4. Store all embeddings
        5. Update processing state for all nodes
        """
        with logfire.span(
            "structural_memory.process_batch",
            batch_size=len(nodes),
        ):
            results: list[NodeProcessingResult] = []
            node_data: list[dict] = []

            # Step 1: Extract triples (deterministic, fast)
            for node in nodes:
                triples = extract_all_triples(node, chart, include_neighbors=False)
                graph_slice = get_graph_slice(node, chart, depth=1)
                derived = compute_derived_triples(
                    node,
                    graph_slice.previous_nodes,
                    graph_slice.next_nodes,
                )
                node_data.append(
                    {
                        "node": node,
                        "triples": triples + derived,
                        "facts": [],
                    }
                )

            # Step 2: Extract facts in parallel using ThreadPoolExecutor
            with ThreadPoolExecutor(
                max_workers=min(len(nodes), BATCH_SIZE)
            ) as executor:
                future_to_idx = {
                    executor.submit(
                        extract_atomic_facts, data["node"], self.llm_provider
                    ): idx
                    for idx, data in enumerate(node_data)
                }

                for future in future_to_idx:
                    idx = future_to_idx[future]
                    try:
                        facts = future.result()
                        node_data[idx]["facts"] = facts
                    except Exception as e:
                        logger.error(
                            f"Failed to extract facts for node "
                            f"{node_data[idx]['node'].id}: {e}"
                        )
                        node_data[idx]["facts"] = []
                        node_data[idx]["error"] = str(e)

            # Step 3 & 4: Batch generate and store embeddings
            if self.embedding_generator:
                self._batch_store_embeddings(node_data, chart)

            # Step 5: Create results and update processing state
            for data in node_data:
                node = data["node"]
                triples_count = len(data["triples"])
                facts_count = len(data["facts"])
                embeddings_count = triples_count + facts_count

                result = NodeProcessingResult(
                    node_id=str(node.id),
                    node_name=node.name,
                    triples_count=triples_count,
                    facts_count=facts_count,
                    embeddings_count=(
                        embeddings_count if self.embedding_generator else 0
                    ),
                    error=data.get("error"),
                )
                results.append(result)

                # Update processing state
                update_processing_state(
                    node=node,
                    chart=chart,
                    triples_count=triples_count,
                    facts_count=facts_count,
                    embeddings_count=result.embeddings_count,
                )

                logfire.info(
                    "structural_memory.node_processed",
                    node_id=str(node.id),
                    triples=triples_count,
                    facts=facts_count,
                    embeddings=result.embeddings_count,
                )

            return results

    def _batch_store_embeddings(self, node_data: list[dict], chart: PxChart) -> None:
        """
        Generate embeddings in batch and store them.

        Collects all texts from all nodes, generates embeddings in one API call,
        then stores them individually.
        """
        if not self.embedding_generator:
            return

        with logfire.span("structural_memory.batch_store_embeddings"):
            # Collect all texts to embed with their metadata
            texts_to_embed: list[str] = []
            text_metadata: list[dict] = []

            for data in node_data:
                node = data["node"]

                # Clear existing memories for this node
                self.vector_store.delete_memories_by_node(str(node.id))

                # Add triples
                for triple in data["triples"]:
                    triple_text = str(triple)
                    texts_to_embed.append(triple_text)
                    text_metadata.append(
                        {
                            "node": node,
                            "type": "knowledge_triple",
                            "content": triple_text,
                            "metadata": {
                                "head": triple.head,
                                "relation": triple.relation,
                                "tail": str(triple.tail),
                            },
                        }
                    )

                # Add facts
                for fact in data["facts"]:
                    texts_to_embed.append(fact.fact)
                    text_metadata.append(
                        {
                            "node": node,
                            "type": "atomic_fact",
                            "content": fact.fact,
                            "metadata": {
                                "source_field": fact.source_field,
                            },
                        }
                    )

            if not texts_to_embed:
                return

            logfire.info(
                "structural_memory.generating_batch_embeddings",
                text_count=len(texts_to_embed),
            )

            # Generate all embeddings in one batch call
            embeddings = self.embedding_generator.generate_embeddings_batch(
                texts_to_embed
            )

            # Store each embedding
            for idx, (text_meta, embedding) in enumerate(
                zip(text_metadata, embeddings)
            ):
                node = text_meta["node"]
                hash_input = (
                    f"{node.id}:{chart.id}:{text_meta['type']}:"
                    f"{text_meta['content']}"
                )
                memory_id = hashlib.md5(hash_input.encode()).hexdigest()

                self.vector_store.store_memory(
                    memory_id=memory_id,
                    node_id=str(node.id),
                    memory_type=text_meta["type"],
                    content=text_meta["content"],
                    embedding=embedding,
                    chart_id=str(chart.id),
                    metadata=text_meta["metadata"],
                )

            logfire.info(
                "structural_memory.batch_embeddings_stored",
                count=len(embeddings),
            )

    def generate_for_charts(self, charts: list[PxChart]) -> list[GenerationResult]:
        """
        Generate structural memory for multiple charts.

        Args:
            charts: List of charts to process

        Returns:
            List of GenerationResult, one per chart
        """
        results = []
        for chart in charts:
            result = self.generate_for_chart(chart)
            results.append(result)
        return results

    def close(self) -> None:
        """Close resources."""
        self.vector_store.close()


def generate_structural_memory(
    chart_ids: list[str],
    llm_model: str = "gpt-4o-mini",
    embedding_model: str = "text-embedding-3-small",
    skip_embeddings: bool = False,
    force_regenerate: bool = False,
) -> list[dict]:
    """
    Convenience function to generate structural memory for charts.

    Args:
        chart_ids: List of chart UUIDs to process
        llm_model: Model for atomic fact extraction
        embedding_model: OpenAI embedding model
        skip_embeddings: If True, skip embedding generation
        force_regenerate: If True, process all nodes regardless of changes

    Returns:
        List of result dictionaries
    """
    from pxcharts.models import PxChart

    generator = StructuralMemoryGenerator(
        llm_model=llm_model,
        embedding_model=embedding_model,
        skip_embeddings=skip_embeddings,
        force_regenerate=force_regenerate,
    )

    try:
        charts = list(PxChart.objects.filter(id__in=chart_ids))
        results = generator.generate_for_charts(charts)
        return [r.to_dict() for r in results]
    finally:
        generator.close()
