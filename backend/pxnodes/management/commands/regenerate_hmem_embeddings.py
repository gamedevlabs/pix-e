"""
Management command to purge and regenerate H-MEM embeddings for a chart.
"""

import logging
from typing import TYPE_CHECKING, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from game_concept.models import GameConcept
from pillars.models import Pillar
from pxcharts.models import PxChart
from pxnodes.llm.context.base.types import EvaluationScope
from pxnodes.llm.context.hmem.strategy import HMEMStrategy
from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
from pxnodes.models import HMEMLayerEmbedding, PxNode

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class Command(BaseCommand):
    """Purge and regenerate H-MEM embeddings for a chart."""

    help = "Purge and regenerate H-MEM embeddings for a chart"

    def add_arguments(self, parser):
        parser.add_argument(
            "--chart-id",
            type=str,
            required=True,
            help="UUID of the chart to regenerate H-MEM embeddings for",
        )
        parser.add_argument(
            "--node-id",
            type=str,
            help="Optional node UUID to regenerate only for a single node",
        )
        parser.add_argument(
            "--user-id",
            type=str,
            help="Optional user UUID to select pillars/game concept",
        )
        parser.add_argument(
            "--clear-only",
            action="store_true",
            help="Clear embeddings but do not regenerate",
        )
        parser.add_argument(
            "--clear-project",
            action="store_true",
            help="Also clear L1 project-level embeddings for the user concept",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="gpt-4o-mini",
            help="LLM model for summaries (default: gpt-4o-mini)",
        )
        parser.add_argument(
            "--embedding-model",
            type=str,
            default="text-embedding-3-small",
            help="Embedding model to use (default: text-embedding-3-small)",
        )
        parser.add_argument(
            "--no-llm",
            action="store_true",
            help="Disable LLM summaries and use heuristic summaries only",
        )

    def handle(self, *args, **options):
        try:
            chart = PxChart.objects.get(id=options["chart_id"])
        except PxChart.DoesNotExist:
            raise CommandError(f"Chart {options['chart_id']} not found")

        user = self._resolve_user(chart, options.get("user_id"))
        game_concept = self._get_game_concept(user)
        pillars = list(Pillar.objects.filter(user=user)) if user else []

        node = None
        if options.get("node_id"):
            try:
                node = PxNode.objects.get(id=options["node_id"])
            except PxNode.DoesNotExist:
                raise CommandError(f"Node {options['node_id']} not found")

        nodes = [node] if node else self._get_chart_nodes(chart)
        if not nodes:
            raise CommandError("No nodes found to regenerate")

        project_id = str(getattr(game_concept, "id", "default"))

        self.stdout.write(self.style.SUCCESS("Clearing H-MEM embeddings..."))
        cleared = self._clear_embeddings(
            chart=chart,
            project_id=project_id,
            clear_project=options["clear_project"],
        )
        self.stdout.write(self.style.SUCCESS(f"Cleared {cleared} embeddings"))

        if options["clear_only"]:
            return

        llm_provider = None
        if not options["no_llm"]:
            llm_provider = LLMProviderAdapter(
                model_name=options["model"],
                temperature=0,
            )

        strategy = HMEMStrategy(
            llm_provider=llm_provider,
            embedding_model=options["embedding_model"],
            auto_embed=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Regenerating H-MEM embeddings for {len(nodes)} nodes..."
            )
        )

        for target_node in nodes:
            scope = EvaluationScope(
                target_node=target_node,
                chart=chart,
                project_pillars=pillars,
                game_concept=game_concept,
            )
            strategy._ensure_embeddings(scope)

        self.stdout.write(self.style.SUCCESS("H-MEM regeneration complete."))

    def _resolve_user(
        self, chart: PxChart, user_id: Optional[str]
    ) -> Optional["AbstractBaseUser"]:
        if user_id:
            try:
                return UserModel.objects.get(id=user_id)
            except UserModel.DoesNotExist:
                raise CommandError(f"User {user_id} not found")

        if chart.owner:
            return chart.owner

        return UserModel.objects.first()

    def _get_game_concept(
        self, user: Optional["AbstractBaseUser"]
    ) -> Optional[GameConcept]:
        if not user:
            return None
        return GameConcept.objects.filter(user=user.pk, is_current=True).first()

    def _get_chart_nodes(self, chart: PxChart) -> list[PxNode]:
        containers = chart.containers.filter(content__isnull=False)
        node_ids = containers.values_list("content_id", flat=True)
        return list(PxNode.objects.filter(id__in=node_ids))

    def _clear_embeddings(
        self, chart: PxChart, project_id: str, clear_project: bool
    ) -> int:
        cleared = 0
        chart_qs = HMEMLayerEmbedding.objects.filter(chart=chart)
        cleared += chart_qs.count()
        chart_qs.delete()

        if clear_project:
            project_qs = HMEMLayerEmbedding.objects.filter(
                layer=1,
                positional_index__startswith=f"L1.{project_id}.",
            )
            cleared += project_qs.count()
            project_qs.delete()

        return cleared
