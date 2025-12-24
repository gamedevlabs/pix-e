"""
Precompute context artifacts for a chart and strategy.
"""

from __future__ import annotations

from typing import Optional

import logfire
from django.core.management.base import BaseCommand, CommandError

from game_concept.models import GameConcept
from pillars.models import Pillar
from pxcharts.models import PxChart
from pxnodes.llm.context.artifacts import ArtifactInventory
from pxnodes.llm.context.base.types import StrategyType
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
from pxnodes.llm.context.shared.graph_retrieval import get_full_path
from pxnodes.llm.context.strategy_needs import get_strategy_needs
from pxnodes.models import PxNode


class Command(BaseCommand):
    help = "Precompute context artifacts for a chart and strategy"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--chart-id",
            type=str,
            required=True,
            help="UUID of the chart to precompute artifacts for",
        )
        parser.add_argument(
            "--strategy",
            type=str,
            default=StrategyType.STRUCTURAL_MEMORY.value,
            help=(
                "Strategy type (full_context, structural_memory, simple_sm, "
                "hierarchical_graph, hmem, combined)"
            ),
        )
        parser.add_argument(
            "--node-id",
            type=str,
            help="Optional node id (required to precompute path artifacts)",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="gpt-4o-mini",
            help="LLM model to use (default: gpt-4o-mini)",
        )
        parser.add_argument(
            "--skip-llm",
            action="store_true",
            help="Skip LLM usage (facts/triples will be empty; summaries fallback)",
        )
        parser.add_argument(
            "--scope",
            type=str,
            default="all",
            help="Precompute scope: global | node | all (default: all)",
        )

    def handle(self, *args, **options) -> None:
        chart = self._get_chart(options["chart_id"])
        strategy_type = self._parse_strategy(options["strategy"])
        needs = get_strategy_needs(strategy_type)

        llm_provider = None
        if not options["skip_llm"]:
            llm_provider = LLMProviderAdapter(
                model_name=options["model"],
                temperature=0,
            )

        inventory = ArtifactInventory(llm_provider=llm_provider)

        scope = options.get("scope", "all")
        with logfire.span(
            "context.precompute",
            chart_id=str(chart.id),
            strategy=strategy_type.value,
            scope=scope,
        ):
            nodes = self._get_chart_nodes(chart)
            if needs.node_artifacts and scope in {"node", "all"}:
                inventory.get_or_build_node_artifacts(
                    chart=chart, nodes=nodes, artifact_types=needs.node_artifacts
                )

            if needs.chart_artifacts and scope in {"global", "all"}:
                inventory.get_or_build_chart_artifacts(
                    chart=chart, artifact_types=needs.chart_artifacts
                )

            concept = self._get_game_concept(chart)
            if concept and needs.concept_artifacts and scope in {"global", "all"}:
                inventory.get_or_build_concept_artifacts(
                    concept_id=str(concept.id),
                    concept_text=concept.content or "",
                    artifact_types=needs.concept_artifacts,
                    project_id=str(concept.id),
                )

            pillars = self._get_pillars(chart)
            if pillars and needs.pillar_artifacts and scope in {"global", "all"}:
                for pillar in pillars:
                    inventory.get_or_build_pillar_artifacts(
                        pillar_id=str(pillar.id),
                        pillar_name=pillar.name or "",
                        pillar_description=pillar.description or "",
                        artifact_types=needs.pillar_artifacts,
                        project_id=str(getattr(pillar.project, "id", "")) or "",
                    )

            if needs.path_artifacts and scope in {"node", "all"}:
                if not options.get("node_id"):
                    self.stdout.write(
                        self.style.WARNING(
                            "Path artifacts requested but --node-id not provided. "
                            "Skipping path artifacts."
                        )
                    )
                else:
                    target_node = self._get_node(options["node_id"])
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Artifacts precomputed for strategy '{strategy_type.value}' "
                f"on chart '{chart.name}'."
            )
        )

    def _parse_strategy(self, strategy: str) -> StrategyType:
        try:
            return StrategyType(strategy)
        except ValueError as exc:
            raise CommandError(f"Unknown strategy '{strategy}'") from exc

    def _get_chart(self, chart_id: str) -> PxChart:
        try:
            return PxChart.objects.get(id=chart_id)
        except PxChart.DoesNotExist as exc:
            raise CommandError(f"Chart {chart_id} not found") from exc

    def _get_node(self, node_id: str) -> PxNode:
        try:
            return PxNode.objects.get(id=node_id)
        except PxNode.DoesNotExist as exc:
            raise CommandError(f"Node {node_id} not found") from exc

    def _get_chart_nodes(self, chart: PxChart) -> list[PxNode]:
        node_ids = chart.containers.filter(content__isnull=False).values_list(
            "content_id", flat=True
        )
        return list(PxNode.objects.filter(id__in=node_ids))

    def _get_game_concept(self, chart: PxChart) -> Optional[GameConcept]:
        return getattr(chart, "project", None)

    def _get_pillars(self, chart: PxChart) -> list[Pillar]:
        project = getattr(chart, "project", None)
        if not project:
            return []
        return list(Pillar.objects.filter(project=project))
