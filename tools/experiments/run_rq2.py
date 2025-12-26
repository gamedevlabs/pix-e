import argparse
import csv
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import django
import logfire


def _parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        return [row for row in reader]


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes", "y"}


@dataclass
class StrategyRunSummary:
    strategy: str
    precompute_ms: int
    eval_total_ms: int
    eval_total_tokens: int
    target_count: int


def _resolve_chart(chart_id_raw: str):
    from pxcharts.models import PxChart

    try:
        try:
            chart_id = uuid.UUID(chart_id_raw)
        except ValueError:
            chart_id = uuid.UUID(hex=chart_id_raw)
        return PxChart.objects.get(id=chart_id)
    except Exception as exc:
        raise SystemExit(f"Chart not found: {chart_id_raw} ({exc})")


def _get_project_context(chart):
    from game_concept.utils import get_current_game_concept, get_current_project
    from pillars.models import Pillar

    owner = getattr(chart, "owner", None)
    project = get_current_project(owner) if owner else None
    project_context = chart.project or project
    concept = get_current_game_concept(project_context)
    pillars = list(Pillar.objects.filter(project=project_context)) if project_context else []
    return project_context, concept, pillars


def _reset_cache(chart, project_context, scope: str) -> None:
    from pxnodes.models import (
        ArtifactEmbedding,
        ContextArtifact,
        HMEMLayerEmbedding,
        StructuralMemoryState,
    )

    with logfire.span("rq2.reset_cache", chart_id=str(chart.id), scope=scope):
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
            global_filters = ContextArtifact.objects.filter(
                scope_type="chart",
                chart=chart,
            )
            if project_context:
                global_filters = global_filters | ContextArtifact.objects.filter(
                    scope_type__in=["concept", "pillar"],
                    project_id=str(project_context.id),
                )

            ArtifactEmbedding.objects.filter(artifact__in=global_filters).delete()
            global_filters.delete()

            if project_context:
                HMEMLayerEmbedding.objects.filter(
                    chart__isnull=True,
                    positional_index__startswith=f"L1.{project_context.id}.",
                ).delete()


def _precompute(
    chart,
    project_context,
    concept,
    pillars,
    strategy_type,
    llm_model,
    embedding_model,
    scope,
    target_node_ids,
) -> None:
    from pxnodes.llm.context.artifacts import ArtifactInventory
    from pxnodes.llm.context.llm_adapter import LLMProviderAdapter
    from pxnodes.llm.context.shared.graph_retrieval import get_full_path
    from pxnodes.llm.context.strategy_needs import get_strategy_needs
    from pxnodes.models import PxNode

    needs = get_strategy_needs(strategy_type)
    llm_provider = LLMProviderAdapter(model_name=llm_model, temperature=0)
    inventory = ArtifactInventory(llm_provider=llm_provider)

    containers = chart.containers.select_related("content").filter(
        content__isnull=False
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

    if concept and needs.concept_artifacts and scope in {"global", "all"}:
        inventory.get_or_build_concept_artifacts(
            concept_id=str(concept.id),
            concept_text=concept.content or "",
            artifact_types=needs.concept_artifacts,
            project_id=str(getattr(project_context, "id", "")) or "",
        )

    if pillars and needs.pillar_artifacts and scope in {"global", "all"}:
        for pillar in pillars:
            inventory.get_or_build_pillar_artifacts(
                pillar_id=str(pillar.id),
                pillar_name=pillar.name or "",
                pillar_description=pillar.description or "",
                artifact_types=needs.pillar_artifacts,
                project_id=str(getattr(project_context, "id", "")) or "",
            )

    if needs.path_artifacts and scope in {"node", "all"}:
        for node_id in target_node_ids:
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
        from pxnodes.llm.context.base.types import EvaluationScope
        from pxnodes.llm.context.hmem.strategy import HMEMStrategy

        strategy = HMEMStrategy(
            llm_provider=llm_provider,
            embedding_model=embedding_model,
            auto_embed=True,
        )
        for node_id in target_node_ids:
            target_node = PxNode.objects.get(id=node_id)
            scope_obj = EvaluationScope(
                target_node=target_node,
                chart=chart,
                project=project_context,
                project_pillars=pillars,
                game_concept=concept,
            )
            strategy._ensure_embeddings(scope_obj)


def _evaluate_nodes(
    chart,
    project_context,
    concept,
    pillars,
    strategy_type,
    llm_model,
    execution_mode,
    target_node_ids,
    node_parallelism: int,
) -> list[dict[str, Any]]:
    import asyncio

    from llm.providers.manager import ModelManager
    from pxnodes.llm.context.shared import create_llm_provider
    from pxnodes.llm.workflows import (
        PxNodesCoherenceMonolithicWorkflow,
        PxNodesCoherenceWorkflow,
    )
    from pxnodes.models import PxNode

    node_map = {
        str(node.id): node
        for node in PxNode.objects.filter(id__in=target_node_ids)
    }

    llm_provider = create_llm_provider(model_name=llm_model, temperature=0)
    model_manager = ModelManager()

    if execution_mode == "agentic":
        workflow = PxNodesCoherenceWorkflow(
            model_manager=model_manager,
            strategy_type=strategy_type,
            llm_provider=llm_provider,
        )
    else:
        workflow = PxNodesCoherenceMonolithicWorkflow(
            model_manager=model_manager,
            strategy_type=strategy_type,
            llm_provider=llm_provider,
        )

    async def _run_all() -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(max(1, node_parallelism))

        async def _run_one(node_id: str) -> dict[str, Any]:
            async with semaphore:
                node = node_map.get(node_id)
                if node is None:
                    raise ValueError(f"Node not found: {node_id}")
                result = await workflow.evaluate_node(
                    node=node,
                    chart=chart,
                    model_id=llm_model,
                    project=project_context,
                    project_pillars=pillars,
                    game_concept=concept,
                )
                return result.model_dump()

        tasks = [asyncio.create_task(_run_one(node_id)) for node_id in target_node_ids]
        return await asyncio.gather(*tasks)

    return asyncio.run(_run_all())


def _write_outputs(
    output_dir: Path,
    run_metadata: dict[str, Any],
    strategy_summaries: list[StrategyRunSummary],
    node_results: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(run_metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    strategy_csv = output_dir / "by_strategy.csv"
    with strategy_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "precompute_ms",
                "eval_total_ms",
                "eval_total_tokens",
                "target_count",
            ],
        )
        writer.writeheader()
        for row in strategy_summaries:
            writer.writerow(row.__dict__)

    node_path = output_dir / "by_node.json"
    node_path.write_text(
        json.dumps(node_results, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RQ2 evaluation sweep")
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument(
        "--strategies",
        default="full_context,structural_memory,simple_sm,hierarchical_graph,hmem",
    )
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    parser.add_argument(
        "--execution-mode",
        choices=["monolithic", "agentic"],
        default="monolithic",
    )
    parser.add_argument("--scope", choices=["global", "node", "all"], default="all")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--node-parallelism",
        type=int,
        default=5,
        help="How many target nodes to evaluate in parallel per strategy.",
    )
    parser.add_argument(
        "--skip-precompute",
        action="store_true",
        help="Reuse existing cache and skip cache reset/precompute steps.",
    )

    args = parser.parse_args()

    chart = _resolve_chart(args.chart_id)
    project_context, concept, pillars = _get_project_context(chart)

    rows = _parse_csv(Path(args.annotations))
    targets = [r for r in rows if _is_truthy(r.get("is_target", ""))]
    if not targets:
        raise SystemExit("No targets with is_target=true found in annotations CSV")

    target_node_ids = [t["node_id"] for t in targets]
    target_node_titles = {t["node_id"]: t.get("node_title", "") for t in targets}

    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    from pxnodes.llm.context.base.types import StrategyType

    strategy_types = []
    for strategy in strategies:
        try:
            strategy_types.append(StrategyType(strategy))
        except ValueError:
            raise SystemExit(f"Unknown strategy: {strategy}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"docs/experiments/rq2_run_{timestamp}")

    run_metadata = {
        "chart_id": str(chart.id),
        "chart_name": chart.name,
        "execution_mode": args.execution_mode,
        "strategies": strategies,
        "model": args.model,
        "embedding_model": args.embedding_model,
        "scope": args.scope,
        "skip_precompute": args.skip_precompute,
        "targets": [
            {"node_id": node_id, "node_title": target_node_titles.get(node_id, "")}
            for node_id in target_node_ids
        ],
        "started_at": timestamp,
    }

    strategy_summaries: list[StrategyRunSummary] = []
    node_results: list[dict[str, Any]] = []

    with logfire.span("rq2.run", chart_id=str(chart.id), strategies=strategies):
        for strategy_type in strategy_types:
            with logfire.span(
                "rq2.strategy", strategy=strategy_type.value, chart_id=str(chart.id)
            ):
                effective_parallelism = args.node_parallelism
                if (
                    strategy_type.value == "structural_memory"
                    and args.node_parallelism > 1
                ):
                    effective_parallelism = 1
                    print(
                        "Note: structural_memory uses a sqlite vector store; "
                        "running nodes sequentially to avoid database locks."
                    )

                if args.skip_precompute:
                    precompute_ms = 0
                else:
                    _reset_cache(chart, project_context, args.scope)

                    precompute_start = time.time()
                    _precompute(
                        chart=chart,
                        project_context=project_context,
                        concept=concept,
                        pillars=pillars,
                        strategy_type=strategy_type,
                        llm_model=args.model,
                        embedding_model=args.embedding_model,
                        scope=args.scope,
                        target_node_ids=target_node_ids,
                    )
                    precompute_ms = int((time.time() - precompute_start) * 1000)

                eval_start = time.time()
                results = _evaluate_nodes(
                    chart=chart,
                    project_context=project_context,
                    concept=concept,
                    pillars=pillars,
                    strategy_type=strategy_type,
                    llm_model=args.model,
                    execution_mode=args.execution_mode,
                    target_node_ids=target_node_ids,
                    node_parallelism=effective_parallelism,
                )
                eval_ms = int((time.time() - eval_start) * 1000)

                eval_total_tokens = sum(r.get("total_tokens", 0) for r in results)

                strategy_summaries.append(
                    StrategyRunSummary(
                        strategy=strategy_type.value,
                        precompute_ms=precompute_ms,
                        eval_total_ms=eval_ms,
                        eval_total_tokens=eval_total_tokens,
                        target_count=len(results),
                    )
                )

                for result in results:
                    node_results.append(
                        {
                            "strategy": strategy_type.value,
                            "node_id": result.get("node_id"),
                            "node_name": result.get("node_name"),
                            "overall_score": result.get("overall_score"),
                            "is_coherent": result.get("is_coherent"),
                            "execution_time_ms": result.get("execution_time_ms"),
                            "total_tokens": result.get("total_tokens"),
                            "dimensions": result,
                        }
                    )

    run_metadata["finished_at"] = time.strftime("%Y%m%d_%H%M%S")

    _write_outputs(output_dir, run_metadata, strategy_summaries, node_results)
    print(f"Saved results to {output_dir}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()
    raise SystemExit(main())
