"""
Management command to test the Structural Memory system end-to-end.

Tests:
1. Knowledge Triple extraction
2. Atomic Fact extraction (with LLM)
3. Embedding generation
4. Vector database storage
5. Similarity search
6. Logfire integration

Usage:
    python manage.py test_structural_memory --node-id <uuid> --chart-id <uuid>
    python manage.py test_structural_memory --auto  # Uses first available node/chart
"""

import hashlib
import logging
from typing import Any, Optional

import logfire
from django.core.management.base import BaseCommand, CommandError

from pxcharts.models import PxChart
from pxnodes.llm.context.facts import AtomicFact, extract_atomic_facts
from pxnodes.llm.context.graph_retrieval import get_graph_slice
from pxnodes.llm.context.structural_memory import StructuralMemoryContext
from pxnodes.llm.context.triples import compute_derived_triples, extract_all_triples
from pxnodes.llm.context.vector_store import VectorStore
from pxnodes.models import PxNode

logger = logging.getLogger(__name__)


class MockLLMProvider:
    """Mock LLM provider for testing without actual LLM calls."""

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate mock atomic facts."""
        # Return a simple formatted response
        return (
            "1. This node involves a specific gameplay mechanic.\n"
            "2. The player encounters this node during their journey.\n"
            "3. This node has specific gameplay components attached."
        )


class EmbeddingGenerator:
    """Simple embedding generator for testing."""

    @staticmethod
    def generate_embedding(text: str, dimension: int = 1536) -> list[float]:
        """
        Generate a deterministic embedding from text using hashing.

        For production, you'd use OpenAI embeddings, but this is sufficient for testing.
        """
        # Use hash of text to generate consistent embeddings
        hash_bytes = hashlib.sha256(text.encode()).digest()

        # Convert to floats in range [-1, 1]
        embedding = []
        for i in range(dimension):
            byte_idx = i % len(hash_bytes)
            value = (hash_bytes[byte_idx] / 255.0) * 2 - 1  # Normalize to [-1, 1]
            embedding.append(value)

        return embedding


class Command(BaseCommand):
    """Test the Structural Memory system end-to-end."""

    help = "Test structural memory extraction, embedding, and storage"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--node-id",
            type=str,
            help="UUID of the node to test with",
        )
        parser.add_argument(
            "--chart-id",
            type=str,
            help="UUID of the chart containing the node",
        )
        parser.add_argument(
            "--auto",
            action="store_true",
            help="Automatically select first available node and chart",
        )
        parser.add_argument(
            "--skip-llm",
            action="store_true",
            help=(
                "Skip LLM-based atomic fact extraction "
                "(only use deterministic triples)"
            ),
        )
        parser.add_argument(
            "--no-embeddings",
            action="store_true",
            help="Skip embedding generation and storage",
        )

    def handle(self, *args, **options):
        """Execute the test."""
        with logfire.span("test_structural_memory", level="info"):
            try:
                # 1. Get node and chart
                node, chart = self._get_node_and_chart(options)

                self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Testing Structural Memory for Node: {node.name}"
                    )
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Chart: {chart.name if chart else 'None'}")
                )
                self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))

                # 2. Extract graph slice
                self._test_graph_slice(node, chart)

                # 3. Extract knowledge triples
                triples = self._test_knowledge_triples(node, chart)

                # 4. Extract atomic facts (optional)
                facts = []
                if not options["skip_llm"]:
                    facts = self._test_atomic_facts(node)

                # 5. Test derived triples
                self._test_derived_triples(node, chart)

                # 6. Build full context
                self._test_context_building(node, chart, options["skip_llm"])

                # 7. Test embeddings and vector storage
                if not options["no_embeddings"]:
                    self._test_vector_storage(node, chart, triples, facts)

                # 8. Get statistics
                self._show_statistics(node, chart, options["skip_llm"])

                self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
                self.stdout.write(
                    self.style.SUCCESS("✅ All tests completed successfully!")
                )
                self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))

            except Exception as e:
                logfire.error("test_structural_memory_failed", error=str(e))
                raise CommandError(f"Test failed: {e}")

    def _get_node_and_chart(self, options):
        """Get the node and chart for testing."""
        with logfire.span("get_test_data"):
            if options["auto"]:
                # Get first node with a chart
                node = PxNode.objects.first()
                if not node:
                    raise CommandError("No nodes found in database")

                # Try to find a chart containing this node
                chart = (
                    PxChart.objects.filter(containers__content=node).first()
                    or PxChart.objects.first()
                )

                if chart:
                    # If chart doesn't contain node, get first node from chart
                    if not chart.containers.filter(content=node).exists():
                        container_with_content = chart.containers.filter(
                            content__isnull=False
                        ).first()
                        if container_with_content:
                            node = container_with_content.content

                logfire.info(
                    "auto_selected_test_data",
                    node_id=str(node.id),
                    node_name=node.name,
                    chart_id=str(chart.id) if chart else None,
                    chart_name=chart.name if chart else None,
                )

            else:
                if not options["node_id"]:
                    raise CommandError("--node-id required (or use --auto)")

                try:
                    node = PxNode.objects.get(id=options["node_id"])
                except PxNode.DoesNotExist:
                    raise CommandError(f"Node {options['node_id']} not found")

                chart = None
                if options["chart_id"]:
                    try:
                        chart = PxChart.objects.get(id=options["chart_id"])
                    except PxChart.DoesNotExist:
                        raise CommandError(f"Chart {options['chart_id']} not found")

            return node, chart

    def _test_graph_slice(self, node: PxNode, chart: Optional[PxChart]):
        """Test graph slice retrieval."""
        self.stdout.write(self.style.WARNING("\n[1] Testing Graph Slice Retrieval"))

        if not chart:
            self.stdout.write("   ⚠️  No chart provided, skipping graph slice")
            return

        with logfire.span("graph_slice_extraction"):
            graph_slice = get_graph_slice(node, chart, depth=1)

            self.stdout.write(f"   Target: {graph_slice.target.name}")
            self.stdout.write(f"   Previous nodes: {len(graph_slice.previous_nodes)}")
            for prev in graph_slice.previous_nodes:
                self.stdout.write(f"      ← {prev.name}")

            self.stdout.write(f"   Next nodes: {len(graph_slice.next_nodes)}")
            for next_node in graph_slice.next_nodes:
                self.stdout.write(f"      → {next_node.name}")

            logfire.info(
                "graph_slice_extracted",
                target_node=node.name,
                previous_count=len(graph_slice.previous_nodes),
                next_count=len(graph_slice.next_nodes),
            )

    def _test_knowledge_triples(self, node: PxNode, chart: Optional[PxChart]):
        """Test knowledge triple extraction."""
        self.stdout.write(
            self.style.WARNING("\n[2] Testing Knowledge Triple Extraction")
        )

        with logfire.span("knowledge_triple_extraction"):
            triples = extract_all_triples(node, chart, include_neighbors=False)

            self.stdout.write(f"   Extracted {len(triples)} triples:")
            for triple in triples[:10]:  # Show first 10
                self.stdout.write(f"      {triple}")

            if len(triples) > 10:
                self.stdout.write(f"      ... and {len(triples) - 10} more")

            logfire.info(
                "knowledge_triples_extracted",
                node_id=str(node.id),
                triple_count=len(triples),
                sample_triples=[str(t) for t in triples[:5]],
            )

            return triples

    def _test_atomic_facts(self, node: PxNode):
        """Test atomic fact extraction."""
        self.stdout.write(
            self.style.WARNING("\n[3] Testing Atomic Fact Extraction (Mock LLM)")
        )

        with logfire.span("atomic_fact_extraction"):
            llm_provider = MockLLMProvider()
            facts = extract_atomic_facts(node, llm_provider)

            self.stdout.write(f"   Extracted {len(facts)} facts:")
            for fact in facts:
                self.stdout.write(f"      • {fact.fact}")

            logfire.info(
                "atomic_facts_extracted",
                node_id=str(node.id),
                fact_count=len(facts),
                facts=[f.fact for f in facts],
            )

            return facts

    def _test_derived_triples(self, node: PxNode, chart: Optional[PxChart]):
        """Test derived triple computation."""
        self.stdout.write(
            self.style.WARNING("\n[4] Testing Derived Triple Computation")
        )

        if not chart:
            self.stdout.write("   ⚠️  No chart provided, skipping derived triples")
            return []

        with logfire.span("derived_triple_computation"):
            graph_slice = get_graph_slice(node, chart, depth=1)
            derived = compute_derived_triples(
                node,
                graph_slice.previous_nodes,
                graph_slice.next_nodes,
            )

            self.stdout.write(f"   Computed {len(derived)} derived triples:")
            for triple in derived:
                self.stdout.write(f"      {triple}")

            logfire.info(
                "derived_triples_computed",
                node_id=str(node.id),
                derived_count=len(derived),
                sample_derived=[str(t) for t in derived[:5]],
            )

            return derived

    def _test_context_building(
        self, node: PxNode, chart: Optional[PxChart], skip_llm: bool
    ):
        """Test full context building."""
        self.stdout.write(self.style.WARNING("\n[5] Testing Full Context Building"))

        if not chart:
            self.stdout.write("   ⚠️  No chart provided, skipping context building")
            return

        with logfire.span("context_building"):
            llm_provider = None if skip_llm else MockLLMProvider()
            context_builder = StructuralMemoryContext(
                llm_provider=llm_provider,
                skip_fact_extraction=skip_llm,
            )

            result = context_builder.build(node, chart, depth=1)

            self.stdout.write(f"   Context length: {len(result.context)} characters")
            self.stdout.write(f"   Total triples: {result.triple_count}")
            self.stdout.write(f"   Atomic facts: {result.fact_count}")
            self.stdout.write(f"   Neighbor nodes: {result.neighbor_count}")

            # Show first 500 chars of context
            self.stdout.write("\n   Context preview:")
            preview = result.context[:500].replace("\n", "\n   ")
            self.stdout.write(f"   {preview}...")

            logfire.info(
                "context_built",
                node_id=str(node.id),
                context_length=len(result.context),
                triple_count=result.triple_count,
                fact_count=result.fact_count,
                neighbor_count=result.neighbor_count,
            )

    def _test_vector_storage(
        self,
        node: PxNode,
        chart: Optional[PxChart],
        triples: list,
        facts: list[AtomicFact],
    ):
        """Test embedding generation and vector storage."""
        self.stdout.write(self.style.WARNING("\n[6] Testing Vector Storage"))

        with logfire.span("vector_storage"):
            vector_store = VectorStore()

            if not vector_store.vec_enabled:
                self.stdout.write(
                    self.style.ERROR(
                        "   ⚠️  sqlite-vec not available, vector search disabled"
                    )
                )
                logfire.warning("vector_storage_disabled")
                return

            embedding_gen = EmbeddingGenerator()

            # Store triples
            triple_count = 0
            for triple in triples:
                triple_text = str(triple)
                embedding = embedding_gen.generate_embedding(triple_text)

                memory_id = hashlib.md5(triple_text.encode()).hexdigest()
                vector_store.store_memory(
                    memory_id=memory_id,
                    node_id=str(node.id),
                    memory_type="knowledge_triple",
                    content=triple_text,
                    embedding=embedding,
                    chart_id=str(chart.id) if chart else None,
                    metadata={
                        "head": triple.head,
                        "relation": triple.relation,
                        "tail": str(triple.tail),
                    },
                )
                triple_count += 1

            self.stdout.write(f"   ✓ Stored {triple_count} knowledge triples")

            # Store facts
            fact_count = 0
            for fact in facts:
                embedding = embedding_gen.generate_embedding(fact.fact)

                memory_id = hashlib.md5(fact.fact.encode()).hexdigest()
                vector_store.store_memory(
                    memory_id=memory_id,
                    node_id=str(node.id),
                    memory_type="atomic_fact",
                    content=fact.fact,
                    embedding=embedding,
                    chart_id=str(chart.id) if chart else None,
                    metadata={
                        "source_field": fact.source_field,
                    },
                )
                fact_count += 1

            self.stdout.write(f"   ✓ Stored {fact_count} atomic facts")

            # Test retrieval
            stored_triples = vector_store.get_memories_by_node(
                str(node.id),
                memory_type="knowledge_triple",
            )
            stored_facts = vector_store.get_memories_by_node(
                str(node.id),
                memory_type="atomic_fact",
            )

            self.stdout.write(
                f"   ✓ Retrieved {len(stored_triples)} triples from database"
            )
            self.stdout.write(f"   ✓ Retrieved {len(stored_facts)} facts from database")

            # Test similarity search
            if triples:
                query_text = str(triples[0])
                query_embedding = embedding_gen.generate_embedding(query_text)
                similar = vector_store.search_similar(
                    query_embedding,
                    limit=3,
                    memory_type="knowledge_triple",
                )
                self.stdout.write(
                    f"   ✓ Similarity search returned {len(similar)} results"
                )
                if similar:
                    self.stdout.write(f"      Most similar: {similar[0]['content']}")

            logfire.info(
                "vector_storage_complete",
                node_id=str(node.id),
                triples_stored=triple_count,
                facts_stored=fact_count,
                triples_retrieved=len(stored_triples),
                facts_retrieved=len(stored_facts),
            )

            vector_store.close()

    def _show_statistics(self, node: PxNode, chart: Optional[PxChart], skip_llm: bool):
        """Show final statistics."""
        self.stdout.write(self.style.WARNING("\n[7] Context Statistics"))

        if not chart:
            return

        # Build context without re-extracting facts
        from pxnodes.llm.context.graph_retrieval import get_graph_slice
        from pxnodes.llm.context.serializer import build_structural_context
        from pxnodes.llm.context.triples import extract_all_triples

        graph_slice = get_graph_slice(node, chart, depth=1)
        triples = extract_all_triples(node, chart, include_neighbors=False)

        # Build context structure without LLM
        context = build_structural_context(
            node, chart, llm_provider=None, skip_fact_extraction=True
        )

        stats = {
            "context_length": len(context),
            "base_triples": len(triples),
            "previous_nodes": len(graph_slice.previous_nodes),
            "next_nodes": len(graph_slice.next_nodes),
        }

        self.stdout.write("   Statistics:")
        for key, value in stats.items():
            self.stdout.write(f"      {key}: {value}")

        logfire.info(
            "context_statistics",
            node_id=str(node.id),
            **stats,  # type: ignore[arg-type]
        )
