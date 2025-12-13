import logging

import logfire
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from pxcharts.models import PxChart

from .models import PxComponent, PxComponentDefinition, PxNode
from .permissions import IsOwnerPermission
from .serializers import (
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeDetailSerializer,
    PxNodeSerializer,
)

logger = logging.getLogger(__name__)


class PxNodeViewSet(viewsets.ModelViewSet):
    serializer_class = PxNodeSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxNode.objects.filter(owner=self.request.user)
        return PxNode.objects.order_by("created_at")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxNodeDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PxComponentDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentDefinitionSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxComponentDefinition.objects.filter(owner=self.request.user)
        return PxComponentDefinition.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PxComponentViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        if self.action == "list":
            return PxComponent.objects.filter(owner=self.request.user)
        return PxComponent.objects.order_by("created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class StructuralMemoryGenerateView(APIView):
    """
    Generate structural memory (knowledge triples, atomic facts, embeddings)
    for nodes in selected charts.

    POST /structural-memory/generate/
    {
        "chart_ids": ["uuid1", "uuid2"],
        "force_regenerate": false,  // optional, default false
        "skip_embeddings": false,   // optional, default false
        "llm_model": "gpt-4o-mini", // optional
        "embedding_model": "text-embedding-3-small"  // optional
    }

    Returns generation results per chart with statistics.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Generate structural memory for selected charts."""
        with logfire.span("structural_memory.api.generate"):
            # Validate input
            chart_ids = request.data.get("chart_ids", [])
            if not chart_ids:
                return Response(
                    {"error": "chart_ids is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get options
            force_regenerate = request.data.get("force_regenerate", False)
            skip_embeddings = request.data.get("skip_embeddings", False)
            llm_model = request.data.get("llm_model", "gpt-4o-mini")
            embedding_model = request.data.get(
                "embedding_model", "text-embedding-3-small"
            )

            # Verify user owns these charts
            charts = PxChart.objects.filter(id__in=chart_ids, owner=request.user)
            if charts.count() != len(chart_ids):
                return Response(
                    {"error": "One or more charts not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            logfire.info(
                "structural_memory.api.generate.start",
                chart_count=len(chart_ids),
                force_regenerate=force_regenerate,
                skip_embeddings=skip_embeddings,
            )

            try:
                # Import here to avoid circular imports
                from pxnodes.llm.context.generator import StructuralMemoryGenerator

                generator = StructuralMemoryGenerator(
                    llm_model=llm_model,
                    embedding_model=embedding_model,
                    skip_embeddings=skip_embeddings,
                    force_regenerate=force_regenerate,
                )

                results = generator.generate_for_charts(list(charts))
                generator.close()

                # Aggregate results
                total_processed = sum(r.processed_count for r in results)
                total_skipped = sum(r.skipped_count for r in results)
                total_triples = sum(r.total_triples for r in results)
                total_facts = sum(r.total_facts for r in results)
                total_embeddings = sum(r.total_embeddings for r in results)

                logfire.info(
                    "structural_memory.api.generate.complete",
                    total_processed=total_processed,
                    total_skipped=total_skipped,
                    total_triples=total_triples,
                    total_facts=total_facts,
                    total_embeddings=total_embeddings,
                )

                return Response(
                    {
                        "success": True,
                        "summary": {
                            "charts_processed": len(results),
                            "nodes_processed": total_processed,
                            "nodes_skipped": total_skipped,
                            "total_triples": total_triples,
                            "total_facts": total_facts,
                            "total_embeddings": total_embeddings,
                        },
                        "charts": [r.to_dict() for r in results],
                    }
                )

            except Exception as e:
                logger.exception("Structural memory generation failed")
                logfire.error(
                    "structural_memory.api.generate.failed",
                    error=str(e),
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class StructuralMemoryStatsView(APIView):
    """
    Get structural memory statistics for charts.

    POST /structural-memory/stats/
    {
        "chart_ids": ["uuid1", "uuid2"]
    }

    Returns processing stats per chart.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Get stats for selected charts."""
        chart_ids = request.data.get("chart_ids", [])
        if not chart_ids:
            return Response(
                {"error": "chart_ids is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify user owns these charts
        charts = PxChart.objects.filter(id__in=chart_ids, owner=request.user)

        from pxnodes.llm.context.change_detection import get_processing_stats

        results = []
        for chart in charts:
            stats = get_processing_stats(chart)
            stats["chart_id"] = str(chart.id)
            stats["chart_name"] = chart.name
            results.append(stats)

        return Response({"charts": results})


class CoherenceEvaluateView(APIView):
    """
    Evaluate node coherence using structural memory retrieval.

    Uses iterative retrieval (Zeng et al. 2024) to gather context
    from knowledge triples and atomic facts, then evaluates nodes
    for coherence issues.

    POST /structural-memory/evaluate/
    {
        "chart_id": "uuid",
        "node_ids": ["uuid1", "uuid2"],  // optional, defaults to all
        "iterations": 3,  // optional, retrieval iterations
        "llm_model": "gpt-4o-mini"  // optional
    }

    Returns evaluation results per node with coherence issues.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Evaluate node coherence for a chart."""
        with logfire.span("structural_memory.api.evaluate"):
            # Validate input
            chart_id = request.data.get("chart_id")
            if not chart_id:
                return Response(
                    {"error": "chart_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get optional parameters
            node_ids = request.data.get("node_ids")
            iterations = request.data.get("iterations", 3)
            llm_model = request.data.get("llm_model", "gpt-4o-mini")

            # Verify user owns the chart
            try:
                chart = PxChart.objects.get(id=chart_id, owner=request.user)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            logfire.info(
                "structural_memory.api.evaluate.start",
                chart_id=str(chart_id),
                node_ids=node_ids,
                iterations=iterations,
            )

            try:
                # Import here to avoid circular imports
                from pxnodes.llm.context.evaluator import NodeCoherenceEvaluator
                from pxnodes.llm.context.llm_adapter import LLMProviderAdapter

                # Create LLM provider
                llm_provider = LLMProviderAdapter(
                    model_name=llm_model,
                    temperature=0.3,  # Lower temperature for evaluation
                )

                # Create evaluator
                evaluator = NodeCoherenceEvaluator(
                    llm_provider=llm_provider,
                    retrieval_iterations=iterations,
                )

                # Evaluate chart
                result = evaluator.evaluate_chart(chart, node_ids=node_ids)
                evaluator.close()

                logfire.info(
                    "structural_memory.api.evaluate.complete",
                    chart_id=str(chart_id),
                    total_nodes=len(result.node_results),
                    coherent_nodes=len(
                        [n for n in result.node_results if n.is_coherent]
                    ),
                )

                return Response(
                    {
                        "success": True,
                        "evaluation": result.to_dict(),
                    }
                )

            except Exception as e:
                logger.exception("Coherence evaluation failed")
                logfire.error(
                    "structural_memory.api.evaluate.failed",
                    error=str(e),
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
