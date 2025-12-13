import logging

import logfire
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import GameConcept
from pillars.models import Pillar
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


class ContextStrategiesView(APIView):
    """
    List available context engineering strategies.

    GET /context/strategies/

    Returns list of available strategies with descriptions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List available context strategies."""
        strategies = [
            {
                "id": "structural_memory",
                "name": "Structural Memory",
                "description": "Knowledge Triples + Atomic Facts (Zeng et al. 2024)",
                "requires_embeddings": True,
                "requires_llm": True,
            },
            {
                "id": "hierarchical_graph",
                "name": "Hierarchical Graph",
                "description": "Deterministic 4-layer graph traversal",
                "requires_embeddings": False,
                "requires_llm": False,
            },
            {
                "id": "hmem",
                "name": "H-MEM",
                "description": "Vector embeddings + positional index routing",
                "requires_embeddings": True,
                "requires_llm": False,
            },
            {
                "id": "combined",
                "name": "Combined",
                "description": "Structural data + hierarchical organization",
                "requires_embeddings": False,
                "requires_llm": True,
            },
        ]
        return Response({"strategies": strategies})


class StrategyEvaluateView(APIView):
    """
    Evaluate node coherence using a specific context strategy.

    POST /context/evaluate/
    {
        "chart_id": "uuid",
        "node_id": "uuid",
        "strategy": "structural_memory",  // or hierarchical_graph, hmem, combined
        "llm_model": "gpt-4o-mini"  // optional
    }

    Returns evaluation result with context metadata.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Evaluate a node using a specific strategy."""
        with logfire.span("context.api.strategy_evaluate"):
            # Validate input
            chart_id = request.data.get("chart_id")
            node_id = request.data.get("node_id")
            strategy = request.data.get("strategy", "structural_memory")
            llm_model = request.data.get("llm_model", "gpt-4o-mini")

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate strategy
            valid_strategies = [
                "structural_memory",
                "hierarchical_graph",
                "hmem",
                "combined",
            ]
            if strategy not in valid_strategies:
                return Response(
                    {"error": f"Invalid strategy. Must be one of: {valid_strategies}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify user owns the chart
            try:
                chart = PxChart.objects.get(id=chart_id, owner=request.user)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node = PxNode.objects.get(id=node_id)
            except PxNode.DoesNotExist:
                return Response(
                    {"error": "Node not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch project-level context for L1 (Domain layer)
            pillars = list(Pillar.objects.filter(user=request.user))
            game_concept = GameConcept.objects.filter(
                user=request.user, is_current=True
            ).first()

            logfire.info(
                "context.api.strategy_evaluate.start",
                chart_id=str(chart_id),
                node_id=str(node_id),
                strategy=strategy,
                pillars_count=len(pillars),
                has_game_concept=game_concept is not None,
            )

            try:
                from pxnodes.llm.context.base import StrategyType
                from pxnodes.llm.context.shared import create_llm_provider
                from pxnodes.llm.context.strategy_evaluator import StrategyEvaluator

                # Create LLM provider
                llm_provider = create_llm_provider(
                    model_name=llm_model,
                    temperature=0.3,
                )

                # Create evaluator
                strategy_type = StrategyType(strategy)
                evaluator = StrategyEvaluator(llm_provider=llm_provider)

                # Evaluate with project context
                result = evaluator.evaluate_node(
                    node=node,
                    chart=chart,
                    strategy_type=strategy_type,
                    project_pillars=pillars,
                    game_concept=game_concept,
                )

                logfire.info(
                    "context.api.strategy_evaluate.complete",
                    node_id=str(node_id),
                    strategy=strategy,
                    is_coherent=result.is_coherent,
                    issues_count=len(result.issues),
                )

                return Response(
                    {
                        "success": True,
                        "result": result.to_dict(),
                    }
                )

            except Exception as e:
                logger.exception("Strategy evaluation failed")
                logfire.error(
                    "context.api.strategy_evaluate.failed",
                    error=str(e),
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class StrategyCompareView(APIView):
    """
    Compare all 4 context strategies for a single node.

    Useful for thesis research to compare strategy effectiveness.

    POST /context/compare/
    {
        "chart_id": "uuid",
        "node_id": "uuid",
        "strategies": ["structural_memory", "hmem"],  // optional, defaults to all
        "llm_model": "gpt-4o-mini"  // optional
    }

    Returns comparison results with all strategies.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Compare strategies for a node."""
        with logfire.span("context.api.strategy_compare"):
            # Validate input
            chart_id = request.data.get("chart_id")
            node_id = request.data.get("node_id")
            strategies_list = request.data.get("strategies")
            llm_model = request.data.get("llm_model", "gpt-4o-mini")

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify user owns the chart
            try:
                chart = PxChart.objects.get(id=chart_id, owner=request.user)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node = PxNode.objects.get(id=node_id)
            except PxNode.DoesNotExist:
                return Response(
                    {"error": "Node not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch project-level context for L1 (Domain layer)
            pillars = list(Pillar.objects.filter(user=request.user))
            game_concept = GameConcept.objects.filter(
                user=request.user, is_current=True
            ).first()

            logfire.info(
                "context.api.strategy_compare.start",
                chart_id=str(chart_id),
                node_id=str(node_id),
                strategies=strategies_list,
                pillars_count=len(pillars),
                has_game_concept=game_concept is not None,
            )

            try:
                from pxnodes.llm.context.base import StrategyType
                from pxnodes.llm.context.shared import create_llm_provider
                from pxnodes.llm.context.strategy_evaluator import StrategyEvaluator

                # Create LLM provider
                llm_provider = create_llm_provider(
                    model_name=llm_model,
                    temperature=0.3,
                )

                # Parse strategies
                if strategies_list:
                    strategy_types = [StrategyType(s) for s in strategies_list]
                else:
                    strategy_types = list(StrategyType)

                # Create evaluator and compare with project context
                evaluator = StrategyEvaluator(llm_provider=llm_provider)
                result = evaluator.compare_strategies(
                    node=node,
                    chart=chart,
                    strategies=strategy_types,
                    project_pillars=pillars,
                    game_concept=game_concept,
                )

                logfire.info(
                    "context.api.strategy_compare.complete",
                    node_id=str(node_id),
                    strategies_compared=len(strategy_types),
                )

                return Response(
                    {
                        "success": True,
                        "comparison": result.to_dict(),
                    }
                )

            except Exception as e:
                logger.exception("Strategy comparison failed")
                logfire.error(
                    "context.api.strategy_compare.failed",
                    error=str(e),
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class ContextBuildView(APIView):
    """
    Build context for a node using a specific strategy (without evaluation).

    Useful for debugging and understanding how each strategy builds context.

    POST /context/build/
    {
        "chart_id": "uuid",
        "node_id": "uuid",
        "strategy": "structural_memory"  // or hierarchical_graph, hmem, combined
    }

    Returns the built context string and metadata.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Build context for a node."""
        with logfire.span("context.api.build"):
            # Validate input
            chart_id = request.data.get("chart_id")
            node_id = request.data.get("node_id")
            strategy = request.data.get("strategy", "structural_memory")

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate strategy
            valid_strategies = [
                "structural_memory",
                "hierarchical_graph",
                "hmem",
                "combined",
            ]
            if strategy not in valid_strategies:
                return Response(
                    {"error": f"Invalid strategy. Must be one of: {valid_strategies}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify user owns the chart
            try:
                chart = PxChart.objects.get(id=chart_id, owner=request.user)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node = PxNode.objects.get(id=node_id)
            except PxNode.DoesNotExist:
                return Response(
                    {"error": "Node not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                from pxnodes.llm.context.base import (
                    EvaluationScope,
                    StrategyRegistry,
                    StrategyType,
                )

                # Create strategy
                strategy_type = StrategyType(strategy)
                strategy_instance = StrategyRegistry.create(strategy_type)

                # Build evaluation scope
                scope = EvaluationScope(
                    target_node=node,
                    chart=chart,
                )

                # Build context
                context_result = strategy_instance.build_context(scope)

                return Response(
                    {
                        "success": True,
                        "strategy": strategy,
                        "context": context_result.context_string,
                        "layers": [
                            {
                                "layer": lc.layer,
                                "name": lc.layer_name,
                                "content": (
                                    lc.content[:500] + "..."
                                    if len(lc.content) > 500
                                    else lc.content
                                ),
                            }
                            for lc in context_result.layers
                        ],
                        "metadata": context_result.metadata,
                        "triples_count": len(context_result.triples),
                        "facts_count": len(context_result.facts),
                    }
                )

            except Exception as e:
                logger.exception("Context building failed")
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
