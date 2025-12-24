import logging

import logfire
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from game_concept.models import GameConcept
from game_concept.utils import get_current_project
from pillars.models import Pillar
from pxcharts.models import PxChart

from .models import (
    ArtifactEmbedding,
    ContextArtifact,
    HMEMLayerEmbedding,
    PxComponent,
    PxComponentDefinition,
    PxNode,
    StructuralMemoryState,
)
from .permissions import IsOwnerPermission
from .serializers import (
    PxComponentDefinitionSerializer,
    PxComponentSerializer,
    PxNodeDetailSerializer,
    PxNodeSerializer,
)
from pxnodes.llm.context.artifacts import ArtifactInventory
from pxnodes.llm.context.base.types import StrategyType
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
from pxnodes.llm.context.shared.graph_retrieval import get_full_path
from pxnodes.llm.context.strategy_needs import get_strategy_needs

logger = logging.getLogger(__name__)


class PxNodeViewSet(viewsets.ModelViewSet):
    serializer_class = PxNodeSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        project = get_current_project(self.request.user)
        queryset = PxNode.objects.filter(owner=self.request.user)
        if project:
            return queryset.filter(project=project)
        return queryset.filter(project__isnull=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PxNodeDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        serializer.save(owner=self.request.user, project=project)


class PxComponentDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentDefinitionSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        project = get_current_project(self.request.user)
        queryset = PxComponentDefinition.objects.filter(owner=self.request.user)
        if project:
            return queryset.filter(project=project)
        return queryset.filter(project__isnull=True)

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        serializer.save(owner=self.request.user, project=project)


class PxComponentViewSet(viewsets.ModelViewSet):
    serializer_class = PxComponentSerializer
    permission_classes = [IsAuthenticated, IsOwnerPermission]

    def get_queryset(self):
        project = get_current_project(self.request.user)
        queryset = PxComponent.objects.filter(owner=self.request.user)
        if project:
            return queryset.filter(node__project=project)
        return queryset.filter(node__project__isnull=True)

    def perform_create(self, serializer):
        project = get_current_project(self.request.user)
        node = serializer.validated_data.get("node")
        if node and node.project_id != (project.id if project else None):
            raise ValidationError("Node does not belong to the active project.")
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
            project = get_current_project(request.user)

            # Verify user owns these charts
            chart_filters = {"id__in": chart_ids, "owner": request.user}
            if project:
                chart_filters["project"] = project
            else:
                chart_filters["project__isnull"] = True
            charts = PxChart.objects.filter(**chart_filters)
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


class ContextArtifactsPrecomputeView(APIView):
    """
    Precompute context artifacts for a chart and strategy.

    POST /context/precompute/
    {
        "chart_id": "uuid",
        "strategy": "structural_memory",
        "node_id": "uuid",  // optional, required if path artifacts needed
        "llm_model": "gpt-4o-mini",  // optional
        "skip_llm": false  // optional
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        chart_id = request.data.get("chart_id")
        if not chart_id:
            return Response(
                {"error": "chart_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        strategy = request.data.get("strategy", StrategyType.STRUCTURAL_MEMORY.value)
        node_id = request.data.get("node_id")
        llm_model = request.data.get("llm_model", "gpt-4o-mini")
        embedding_model = request.data.get("embedding_model", "text-embedding-3-small")
        skip_llm = request.data.get("skip_llm", False)
        scope = request.data.get("scope", "all")  # global | node | all

        try:
            strategy_type = StrategyType(strategy)
        except ValueError:
            return Response(
                {"error": f"Unknown strategy '{strategy}'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_current_project(request.user)
        chart_filters = {"id": chart_id, "owner": request.user}
        if project:
            chart_filters["project"] = project
        else:
            chart_filters["project__isnull"] = True

        chart = PxChart.objects.filter(**chart_filters).first()
        if not chart:
            return Response(
                {"error": "Chart not found or not owned by user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        needs = get_strategy_needs(strategy_type)
        with logfire.span(
            "context.precompute",
            chart_id=str(chart.id),
            strategy=strategy_type.value,
            scope=scope,
        ):
            llm_provider = None
            if not skip_llm:
                llm_provider = LLMProviderAdapter(
                    model_name=llm_model,
                    temperature=0,
                )
            inventory = ArtifactInventory(llm_provider=llm_provider)

            containers = (
                chart.containers.select_related("content")
                .filter(content__isnull=False)
            )
            nodes = [c.content for c in containers if c.content]

            if needs.node_artifacts and scope in {"node", "all"}:
                inventory.get_or_build_node_artifacts(
                    chart=chart,
                    nodes=nodes,
                    artifact_types=needs.node_artifacts,
                )

            if needs.chart_artifacts and scope in {"global", "all"}:
                inventory.get_or_build_chart_artifacts(
                    chart=chart,
                    artifact_types=needs.chart_artifacts,
                )

            concept = chart.project or project
            if concept and needs.concept_artifacts and scope in {"global", "all"}:
                inventory.get_or_build_concept_artifacts(
                    concept_id=str(concept.id),
                    concept_text=concept.content or "",
                    artifact_types=needs.concept_artifacts,
                    project_id=str(concept.id),
                )

            project_pillars = []
            if concept and needs.pillar_artifacts and scope in {"global", "all"}:
                project_pillars = list(Pillar.objects.filter(project=concept))
                for pillar in project_pillars:
                    inventory.get_or_build_pillar_artifacts(
                        pillar_id=str(pillar.id),
                        pillar_name=pillar.name or "",
                        pillar_description=pillar.description or "",
                        artifact_types=needs.pillar_artifacts,
                        project_id=str(concept.id),
                    )

            if needs.path_artifacts and scope in {"node", "all"}:
                if not node_id:
                    return Response(
                        {"error": "node_id is required for path artifacts"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if not chart.containers.filter(content_id=node_id).exists():
                    return Response(
                        {"error": "node_id does not belong to this chart"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                target_node = PxNode.objects.get(id=node_id)
                graph_slice = get_full_path(target_node, chart)
                path_nodes = (
                    graph_slice.previous_nodes
                    + [graph_slice.target]
                    + graph_slice.next_nodes
                )
                inventory.get_or_build_path_artifacts(
                    chart=chart,
                    path_nodes=path_nodes,
                    artifact_types=needs.path_artifacts,
                )

            if needs.requires_embeddings and scope in {"node", "all"}:
                if strategy_type in {StrategyType.HMEM, StrategyType.COMBINED}:
                    if not node_id:
                        return Response(
                            {"error": "node_id is required for embedding precompute"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    target_node = PxNode.objects.get(id=node_id)
                    from pxnodes.llm.context.base.types import EvaluationScope
                    from pxnodes.llm.context.hmem.strategy import HMEMStrategy

                    scope = EvaluationScope(
                        target_node=target_node,
                        chart=chart,
                        project_pillars=project_pillars,
                        game_concept=concept,
                    )
                    hmem_strategy = HMEMStrategy(
                        llm_provider=llm_provider,
                        embedding_model=embedding_model,
                    )
                    hmem_strategy._ensure_embeddings(scope)
                elif strategy_type == StrategyType.STRUCTURAL_MEMORY:
                    if not nodes:
                        return Response(
                            {"error": "No nodes found for this chart"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    from pxnodes.llm.context.base.types import EvaluationScope
                    from pxnodes.llm.context.structural_memory.strategy import (
                        StructuralMemoryStrategy,
                    )

                    target_node = nodes[0]
                    scope = EvaluationScope(
                        target_node=target_node,
                        chart=chart,
                        project_pillars=project_pillars,
                        game_concept=concept,
                    )
                    sm_strategy = StructuralMemoryStrategy(
                        llm_provider=llm_provider,
                        embedding_model=embedding_model,
                    )
                    sm_strategy._ensure_vector_store_memories(scope, nodes)

        return Response(
            {
                "success": True,
                "chart_id": str(chart.id),
                "strategy": strategy_type.value,
                "scope": scope,
            }
        )


class ContextArtifactsResetView(APIView):
    """
    Reset context artifacts for a chart.

    POST /context/precompute/reset/
    {
        "chart_id": "uuid",
        "scope": "global|node|all"  // optional, default all
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        chart_id = request.data.get("chart_id")
        if not chart_id:
            return Response(
                {"error": "chart_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        scope = request.data.get("scope", "all")
        if scope not in {"global", "node", "all"}:
            return Response(
                {"error": "scope must be global, node, or all"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = get_current_project(request.user)
        chart_filters = {"id": chart_id, "owner": request.user}
        if project:
            chart_filters["project"] = project
        else:
            chart_filters["project__isnull"] = True

        chart = PxChart.objects.filter(**chart_filters).first()
        if not chart:
            return Response(
                {"error": "Chart not found or not owned by user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        with logfire.span(
            "context.precompute.reset",
            chart_id=str(chart.id),
            scope=scope,
        ):
            if scope in {"node", "all"}:
                node_artifacts = ContextArtifact.objects.filter(
                    chart=chart, scope_type__in=["node", "path"]
                )
                ArtifactEmbedding.objects.filter(artifact__in=node_artifacts).delete()
                node_artifacts.delete()

                node_ids = list(
                    chart.containers.filter(content__isnull=False).values_list(
                        "content_id", flat=True
                    )
                )
                if node_ids:
                    from pxnodes.llm.context.shared.vector_store import VectorStore

                    vector_store = VectorStore()
                    for node_id in node_ids:
                        vector_store.delete_memories_by_node(
                            str(node_id), chart_id=str(chart.id)
                        )
                    vector_store.close()

                StructuralMemoryState.objects.filter(chart=chart).delete()
                HMEMLayerEmbedding.objects.filter(chart=chart).delete()

            if scope in {"global", "all"}:
                concept = chart.project or project
                global_filters = ContextArtifact.objects.filter(
                    scope_type="chart",
                    chart=chart,
                )
                if concept:
                    global_filters = global_filters | ContextArtifact.objects.filter(
                        scope_type__in=["concept", "pillar"],
                        project_id=str(concept.id),
                    )

                ArtifactEmbedding.objects.filter(artifact__in=global_filters).delete()
                global_filters.delete()

                if concept:
                    HMEMLayerEmbedding.objects.filter(
                        chart__isnull=True,
                        positional_index__startswith=f"L1.{concept.id}.",
                    ).delete()

        return Response(
            {"success": True, "chart_id": str(chart.id), "scope": scope}
        )

        # Verify user owns these charts
        project = get_current_project(request.user)
        chart_filters = {"id__in": chart_ids, "owner": request.user}
        if project:
            chart_filters["project"] = project
        else:
            chart_filters["project__isnull"] = True
        charts = PxChart.objects.filter(**chart_filters)

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
            project = get_current_project(request.user)

            # Verify user owns the chart
            try:
                chart_filters = {"id": chart_id, "owner": request.user}
                if project:
                    chart_filters["project"] = project
                else:
                    chart_filters["project__isnull"] = True
                chart = PxChart.objects.get(**chart_filters)
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
                    temperature=0,
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
                "id": "full_context",
                "name": "Full Context",
                "description": "Full concept, pillars, and path node descriptions",
                "requires_embeddings": False,
                "requires_llm": False,
            },
            {
                "id": "structural_memory",
                "name": "Structural Memory",
                "description": "Mixed memory + iterative retrieval (Zeng et al. 2024)",
                "requires_embeddings": True,
                "requires_llm": True,
            },
            {
                "id": "simple_sm",
                "name": "Simple SM",
                "description": "Full path with summaries, triples, and facts only",
                "requires_embeddings": False,
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
                "description": "SM mixed encoding + H-MEM routing",
                "requires_embeddings": True,
                "requires_llm": True,
            },
        ]
        return Response({"strategies": strategies})


class StrategyEvaluateView(APIView):
    """
    Evaluate node coherence using a specific context strategy.

    Supports both monolithic (single LLM call) and agentic (parallel agents) modes.

    POST /context/evaluate/
    {
        "chart_id": "uuid",
        "node_id": "uuid",
        "strategy": "structural_memory",  // or hierarchical_graph, hmem, combined
        "execution_mode": "monolithic",  // or "agentic" (default: "monolithic")
        "llm_model": "gpt-4o-mini"  // optional
    }

    Returns evaluation result with context metadata.

    Monolithic mode: Single LLM call evaluates all coherence dimensions together.
    Agentic mode: 4 parallel dimension agents (prerequisite, forward,
    internal, contextual).
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Evaluate a node using a specific strategy."""
        # Validate input
        chart_id = request.data.get("chart_id")
        node_id = request.data.get("node_id")
        strategy = request.data.get("strategy", "structural_memory")
        project = get_current_project(request.user)
        execution_mode = request.data.get("execution_mode", "monolithic")
        llm_model = request.data.get("llm_model", "gpt-4o-mini")

        span_name = f"context.evaluate.pxnodes.{strategy}.{execution_mode}"
        with logfire.span(
            span_name,
            feature="pxnodes",
            strategy=strategy,
            execution_mode=execution_mode,
        ):

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate strategy
            valid_strategies = [
                "full_context",
                "structural_memory",
                "simple_sm",
                "hierarchical_graph",
                "hmem",
                "combined",
            ]
            if strategy not in valid_strategies:
                return Response(
                    {"error": f"Invalid strategy. Must be one of: {valid_strategies}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate execution mode
            valid_modes = ["monolithic", "agentic"]
            if execution_mode not in valid_modes:
                return Response(
                    {"error": f"Invalid execution_mode. Must be one of: {valid_modes}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify user owns the chart
            try:
                chart_filters = {"id": chart_id, "owner": request.user}
                if project:
                    chart_filters["project"] = project
                else:
                    chart_filters["project__isnull"] = True
                chart = PxChart.objects.get(**chart_filters)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node_filters = {"id": node_id}
                if project:
                    node_filters["project"] = project
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.get(**node_filters)
            except PxNode.DoesNotExist:
                return Response(
                    {"error": "Node not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch project-level context for L1 (Domain layer)
            pillar_filters = {"user": request.user}
            if project:
                pillar_filters["project"] = project
            else:
                pillar_filters["project__isnull"] = True
            pillars = list(Pillar.objects.filter(**pillar_filters))
            game_concept = GameConcept.objects.filter(
                user=request.user, is_current=True
            ).first()

            logfire.info(
                "context.evaluate.start",
                chart_id=str(chart_id),
                node_id=str(node_id),
                strategy=strategy,
                execution_mode=execution_mode,
                pillars_count=len(pillars),
                has_game_concept=game_concept is not None,
            )

            try:
                from pxnodes.llm.context.base import StrategyType
                from pxnodes.llm.context.shared import create_llm_provider

                # Create LLM provider
                llm_provider = create_llm_provider(
                    model_name=llm_model,
                    temperature=0,
                )

                strategy_type = StrategyType(strategy)

                # Import shared dependencies
                import asyncio

                from llm.providers.manager import ModelManager
                from pxnodes.llm.workflows import (
                    PxNodesCoherenceMonolithicWorkflow,
                    PxNodesCoherenceWorkflow,
                )

                model_manager = ModelManager()

                if execution_mode == "agentic":
                    # Use agentic workflow with 4 parallel dimension agents
                    workflow = PxNodesCoherenceWorkflow(
                        model_manager=model_manager,
                        strategy_type=strategy_type,
                        llm_provider=llm_provider,
                    )

                    # Run async workflow
                    result = asyncio.run(
                        workflow.evaluate_node(
                            node=node,
                            chart=chart,
                            model_id=llm_model,
                            project_pillars=pillars,
                            game_concept=game_concept,
                        )
                    )
                else:
                    # Use monolithic workflow with unified prompt
                    # Same response schema as agentic for fair thesis comparison
                    workflow = PxNodesCoherenceMonolithicWorkflow(
                        model_manager=model_manager,
                        strategy_type=strategy_type,
                        llm_provider=llm_provider,
                    )

                    # Run async workflow
                    result = asyncio.run(
                        workflow.evaluate_node(
                            node=node,
                            chart=chart,
                            model_id=llm_model,
                            project_pillars=pillars,
                            game_concept=game_concept,
                        )
                    )

                logfire.info(
                    "context.evaluate.complete",
                    node_id=str(node_id),
                    strategy=strategy,
                    execution_mode=execution_mode,
                    is_coherent=result.is_coherent,
                    overall_score=result.overall_score,
                    total_issues=result.total_issues,
                )

                return Response(
                    {
                        "success": True,
                        "execution_mode": execution_mode,
                        "result": result.model_dump(),
                    }
                )

            except Exception as e:
                logger.exception("Strategy evaluation failed")
                logfire.error(
                    "context.evaluate.failed",
                    error=str(e),
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )


class StrategyCompareView(APIView):
    """
    Compare all context strategies for a single node.

    Useful for thesis research to compare strategy effectiveness.

    POST /context/compare/
    {
        "chart_id": "uuid",
        "node_id": "uuid",
        "strategies": ["structural_memory", "simple_sm"],  // optional, defaults to all
        "llm_model": "gpt-4o-mini"  // optional
    }

    Returns comparison results with all strategies.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Compare strategies for a node."""
        # Validate input
        chart_id = request.data.get("chart_id")
        node_id = request.data.get("node_id")
        strategies_list = request.data.get("strategies")
        llm_model = request.data.get("llm_model", "gpt-4o-mini")
        project = get_current_project(request.user)

        with logfire.span(
            "context.compare.pxnodes",
            feature="pxnodes",
            strategies=strategies_list,
        ):

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify user owns the chart
            try:
                chart_filters = {"id": chart_id, "owner": request.user}
                if project:
                    chart_filters["project"] = project
                else:
                    chart_filters["project__isnull"] = True
                chart = PxChart.objects.get(**chart_filters)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node_filters = {"id": node_id}
                if project:
                    node_filters["project"] = project
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.get(**node_filters)
            except PxNode.DoesNotExist:
                return Response(
                    {"error": "Node not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch project-level context for L1 (Domain layer)
            pillar_filters = {"user": request.user}
            if project:
                pillar_filters["project"] = project
            else:
                pillar_filters["project__isnull"] = True
            pillars = list(Pillar.objects.filter(**pillar_filters))
            game_concept = GameConcept.objects.filter(
                user=request.user, is_current=True
            ).first()

            logfire.info(
                "context.compare.start",
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
                    temperature=0,
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
                    "context.compare.complete",
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
                    "context.compare.failed",
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
        # Validate input
        chart_id = request.data.get("chart_id")
        node_id = request.data.get("node_id")
        strategy = request.data.get("strategy", "structural_memory")
        project = get_current_project(request.user)

        with logfire.span(
            f"context.build.pxnodes.{strategy}",
            feature="pxnodes",
            strategy=strategy,
        ):

            if not chart_id or not node_id:
                return Response(
                    {"error": "chart_id and node_id are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate strategy
            valid_strategies = [
                "structural_memory",
                "simple_sm",
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
                chart_filters = {"id": chart_id, "owner": request.user}
                if project:
                    chart_filters["project"] = project
                else:
                    chart_filters["project__isnull"] = True
                chart = PxChart.objects.get(**chart_filters)
            except PxChart.DoesNotExist:
                return Response(
                    {"error": "Chart not found or not owned by user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get the node
            try:
                node_filters = {"id": node_id}
                if project:
                    node_filters["project"] = project
                else:
                    node_filters["project__isnull"] = True
                node = PxNode.objects.get(**node_filters)
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
