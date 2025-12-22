"""
Management command to generate and store structural memory with real LLM and embeddings.
"""

import hashlib
import logging
from typing import Optional

import logfire
from django.core.management.base import BaseCommand, CommandError

from pxcharts.models import PxChart
from pxnodes.llm.context.embeddings import OpenAIEmbeddingGenerator
from pxnodes.llm.context.facts import extract_atomic_facts
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
from pxnodes.llm.context.triples import extract_llm_triples_only
from pxnodes.llm.context.vector_store import VectorStore
from pxnodes.models import PxNode

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Generate and store structural memory using real LLM and embeddings."""

    help = "Generate structural memory with real LLM and OpenAI embeddings"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--node-id",
            type=str,
            help="UUID of the node to process",
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
            "--all-nodes",
            action="store_true",
            help="Process all nodes in the chart",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="gpt-4o-mini",
            help="LLM model to use for fact extraction (default: gpt-4o-mini)",
        )
        parser.add_argument(
            "--embedding-model",
            type=str,
            default="text-embedding-3-small",
            help="OpenAI embedding model (default: text-embedding-3-small)",
        )
        parser.add_argument(
            "--skip-embeddings",
            action="store_true",
            help="Skip embedding generation (extract facts only)",
        )
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing memories for the node before generating new ones",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        with logfire.span("generate_structural_memory", level="info"):
            try:
                # Initialize LLM and embedding generators
                llm_provider = LLMProviderAdapter(
                    model_name=options["model"],
                    temperature=0,
                )

                embedding_generator = None
                if not options["skip_embeddings"]:
                    embedding_generator = OpenAIEmbeddingGenerator(
                        model=options["embedding_model"]
                    )

                self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
                self.stdout.write(
                    self.style.SUCCESS("Generating Structural Memory (Production Mode)")
                )
                self.stdout.write(self.style.SUCCESS(f"LLM Model: {options['model']}"))
                if embedding_generator:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Embedding Model: {options['embedding_model']}"
                        )
                    )
                self.stdout.write(self.style.SUCCESS(f"{'='*70}\n"))

                # Get nodes and chart
                nodes, chart = self._get_nodes_and_chart(options)

                # Process each node
                total_triples = 0
                total_facts = 0
                total_embeddings = 0

                for node in nodes:
                    result = self._process_node(
                        node=node,
                        chart=chart,
                        llm_provider=llm_provider,
                        embedding_generator=embedding_generator,
                        clear_existing=options["clear_existing"],
                    )

                    total_triples += result["triples"]
                    total_facts += result["facts"]
                    total_embeddings += result["embeddings"]

                # Summary
                self.stdout.write(self.style.SUCCESS(f"\n{'='*70}"))
                self.stdout.write(self.style.SUCCESS("✅ Generation Complete!"))
                self.stdout.write(self.style.SUCCESS(f"Nodes processed: {len(nodes)}"))
                self.stdout.write(
                    self.style.SUCCESS(f"Total triples generated: {total_triples}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Total facts extracted: {total_facts}")
                )
                if embedding_generator:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Total embeddings stored: {total_embeddings}"
                        )
                    )
                self.stdout.write(self.style.SUCCESS(f"{'='*70}\n"))

            except Exception as e:
                logfire.error("generate_structural_memory_failed", error=str(e))
                raise CommandError(f"Generation failed: {e}")

    def _get_nodes_and_chart(self, options):
        """Get the nodes and chart to process."""
        with logfire.span("get_nodes_and_chart"):
            if options["auto"]:
                # Get first node with a chart
                node = PxNode.objects.first()
                if not node:
                    raise CommandError("No nodes found in database")

                chart = (
                    PxChart.objects.filter(containers__content=node).first()
                    or PxChart.objects.first()
                )

                if chart and not chart.containers.filter(content=node).exists():
                    container_with_content = chart.containers.filter(
                        content__isnull=False
                    ).first()
                    if container_with_content:
                        node = container_with_content.content

                nodes = [node] if node else []

            elif options["all_nodes"]:
                if not options["chart_id"]:
                    raise CommandError("--chart-id required with --all-nodes")

                try:
                    chart = PxChart.objects.get(id=options["chart_id"])
                except PxChart.DoesNotExist:
                    raise CommandError(f"Chart {options['chart_id']} not found")

                # Get all nodes in the chart
                node_ids = chart.containers.filter(content__isnull=False).values_list(
                    "content_id", flat=True
                )
                nodes = list(PxNode.objects.filter(id__in=node_ids))

                if not nodes:
                    raise CommandError(f"No nodes found in chart {chart.name}")

            else:
                if not options["node_id"]:
                    raise CommandError(
                        "--node-id required (or use --auto or --all-nodes)"
                    )

                try:
                    node = PxNode.objects.get(id=options["node_id"])
                    nodes = [node]
                except PxNode.DoesNotExist:
                    raise CommandError(f"Node {options['node_id']} not found")

                chart = None
                if options["chart_id"]:
                    try:
                        chart = PxChart.objects.get(id=options["chart_id"])
                    except PxChart.DoesNotExist:
                        raise CommandError(f"Chart {options['chart_id']} not found")

            return nodes, chart

    def _process_node(
        self,
        node: PxNode,
        chart: Optional[PxChart],
        llm_provider: LLMProviderAdapter,
        embedding_generator: Optional[OpenAIEmbeddingGenerator],
        clear_existing: bool,
    ) -> dict:
        """Process a single node."""
        with logfire.span(
            "process_node",
            node_id=str(node.id),
            node_name=node.name,
        ):
            self.stdout.write(self.style.WARNING(f"\nProcessing: {node.name}"))

            # Clear existing memories if requested
            if clear_existing and embedding_generator:
                vector_store = VectorStore()
                deleted = vector_store.delete_memories_by_node(str(node.id))
                if deleted > 0:
                    self.stdout.write(f"   Cleared {deleted} existing memories")
                vector_store.close()

            # 1. Extract knowledge triples (LLM-only)
            triples = extract_llm_triples_only(node, llm_provider)
            self.stdout.write(f"   ✓ Extracted {len(triples)} knowledge triples")

            # 2. Extract atomic facts (using real LLM)
            facts = extract_atomic_facts(node, llm_provider)
            self.stdout.write(f"   ✓ Extracted {len(facts)} atomic facts (LLM)")

            # 3. Generate and store embeddings
            embeddings_stored = 0
            if embedding_generator:
                embeddings_stored = self._store_embeddings(
                    node=node,
                    chart=chart,
                    triples=triples,
                    derived=[],
                    facts=facts,
                    embedding_generator=embedding_generator,
                )
                self.stdout.write(f"   ✓ Stored {embeddings_stored} embeddings")

            # 5. Show statistics (without re-extracting facts)
            if chart:
                # Build context without LLM to avoid duplicate extraction
                from pxnodes.llm.context.serializer import build_structural_context

                context = build_structural_context(
                    node, chart, llm_provider=None, skip_fact_extraction=True
                )

                self.stdout.write(
                    f"   📊 Context: {len(context)} chars, "
                    f"{len(triples)} triples, "
                    f"{len(facts)} facts"
                )

            logfire.info(
                "node_processed",
                node_id=str(node.id),
                node_name=node.name,
                triples=len(triples),
                facts=len(facts),
                embeddings=embeddings_stored,
            )

            return {
                "triples": len(triples),
                "facts": len(facts),
                "embeddings": embeddings_stored,
            }

    def _store_embeddings(
        self,
        node: PxNode,
        chart: Optional[PxChart],
        triples: list,
        derived: list,
        facts: list,
        embedding_generator: OpenAIEmbeddingGenerator,
    ) -> int:
        """Generate and store embeddings for all memories."""
        with logfire.span("store_embeddings", node_id=str(node.id)):
            vector_store = VectorStore()
            count = 0

            # Store knowledge triples
            for triple in triples + derived:
                triple_text = str(triple)
                embedding = embedding_generator.generate_embedding(triple_text)

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
                count += 1

            # Store atomic facts
            for fact in facts:
                embedding = embedding_generator.generate_embedding(fact.fact)

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
                count += 1

            vector_store.close()
            return count
