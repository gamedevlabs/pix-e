import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import django

def _resolve_concept(project) -> Optional[Any]:
    from game_concept.models import GameConcept

    concept = (
        GameConcept.objects.filter(project=project, is_current=True)
        .order_by("-updated_at")
        .first()
    )
    if concept:
        return concept
    return (
        GameConcept.objects.filter(project=project)
        .order_by("-updated_at")
        .first()
    )


def _run_monolithic(game_text: str, model_id: str) -> Dict[str, Any]:
    from llm.orchestrator import LLMOrchestrator
    from llm.types import LLMRequest

    orchestrator = LLMOrchestrator()
    request = LLMRequest(
        feature="sparc",
        operation="monolithic",
        data={"game_text": game_text},
        mode="monolithic",
        model_id=model_id,
    )
    response = orchestrator.execute(request)
    token_usage = response.metadata.token_usage
    return {
        "success": response.success,
        "results": response.results,
        "execution_time_ms": response.metadata.execution_time_ms,
        "total_tokens": token_usage.total_tokens if token_usage else 0,
        "estimated_cost_eur": 0,
        "errors": [e.message for e in response.errors] if response.errors else [],
        "warnings": [w.message for w in response.warnings] if response.warnings else [],
    }


def _run_router_v2(
    *,
    game_text: str,
    model_id: str,
    user: Any,
    pillar_mode: str,
    context_strategy: str,
    project_id: Optional[int],
) -> Dict[str, Any]:
    import asyncio

    from llm.config import get_config
    from llm.events import EventCollector
    from llm.providers.manager import ModelManager
    from llm.types import LLMRequest
    from sparc.llm.workflows_v2 import SPARCRouterWorkflow

    config = get_config()
    model_manager = ModelManager(config)
    event_collector = EventCollector()

    workflow = SPARCRouterWorkflow(
        model_manager=model_manager,
        config=config,
        event_collector=event_collector,
        evaluation=None,
        user=user,
    )

    request_data: Dict[str, Any] = {
        "game_text": game_text,
        "context": "",
        "pillar_mode": pillar_mode,
        "context_strategy": context_strategy,
    }
    if project_id:
        request_data["project_id"] = project_id

    request = LLMRequest(
        feature="sparc",
        operation="router_v2",
        data=request_data,
        model_id=model_id,
        mode="agentic",
    )

    result = asyncio.run(workflow.run(request, mode="full"))
    return {
        "success": result.success,
        "results": result.aggregated_data,
        "execution_time_ms": result.total_execution_time_ms,
        "total_tokens": result.aggregated_data.get("total_tokens", 0),
        "estimated_cost_eur": 0,
        "errors": [e.message for e in result.errors] if result.errors else [],
        "warnings": [w.message for w in result.warnings] if result.warnings else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RQ1 three-arm SPARC evaluation")
    parser.add_argument("--user-id", type=int, default=2)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of projects processed.",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="Run for a single project id.",
    )

    args = parser.parse_args()

    from django.contrib.auth import get_user_model
    from game_concept.models import Project

    user_model = get_user_model()
    try:
        user = user_model.objects.get(id=args.user_id)
    except user_model.DoesNotExist as exc:
        raise SystemExit(f"User not found: {args.user_id}") from exc

    projects = Project.objects.filter(user=user).order_by("id")
    if args.project_id:
        projects = projects.filter(id=args.project_id)
    if args.limit is not None:
        projects = projects[: max(0, args.limit)]

    if not projects:
        raise SystemExit("No projects found for the requested scope.")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"docs/experiments/rq1_run_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    from llm.logfire_config import get_logfire
    from tools.experiments.rq1_synthesis import run_rq1_synthesis

    run_meta = {
        "user_id": args.user_id,
        "model": args.model,
        "project_id": args.project_id,
        "limit": args.limit,
        "started_at": timestamp,
    }

    results: list[Dict[str, Any]] = []
    logfire = get_logfire()

    with logfire.span(
        "rq1.run",
        user_id=args.user_id,
        model=args.model,
        project_id=args.project_id or "",
        limit=args.limit or "",
    ):
        for project in projects:
            concept = _resolve_concept(project)
            if not concept:
                continue

            game_text = concept.content

            with logfire.span(
                "rq1.concept",
                project_id=str(project.id),
                project_name=project.name,
                concept_id=str(concept.id),
            ):
                with logfire.span("rq1.mode.monolithic"):
                    monolithic = _run_monolithic(game_text, args.model)
                with logfire.span("rq1.mode.agentic_full_text"):
                    agentic_full = _run_router_v2(
                        game_text=game_text,
                        model_id=args.model,
                        user=user,
                        pillar_mode="none",
                        context_strategy="full_text",
                        project_id=project.id,
                    )
                with logfire.span("rq1.mode.agentic_routed"):
                    agentic_routed = _run_router_v2(
                        game_text=game_text,
                        model_id=args.model,
                        user=user,
                        pillar_mode="smart",
                        context_strategy="router",
                        project_id=project.id,
                    )

            with logfire.span("rq1.synthesis"):
                monolithic_synth = run_rq1_synthesis(
                    model_name=args.model,
                    mode="monolithic",
                    results=monolithic.get("results", {}),
                )
                agentic_full_synth = run_rq1_synthesis(
                    model_name=args.model,
                    mode="agentic",
                    results=agentic_full.get("results", {}),
                )
                agentic_routed_synth = run_rq1_synthesis(
                    model_name=args.model,
                    mode="agentic",
                    results=agentic_routed.get("results", {}),
                )

            results.append(
                {
                    "project_id": project.id,
                    "project_name": project.name,
                    "project_description": project.description,
                    "concept_id": concept.id,
                    "game_text": game_text,
                    "monolithic": monolithic,
                    "agentic_full_text": agentic_full,
                    "agentic_routed": agentic_routed,
                    "rq1_synthesis": {
                        "monolithic": monolithic_synth,
                        "agentic_full_text": agentic_full_synth,
                        "agentic_routed": agentic_routed_synth,
                    },
                }
            )

    run_meta["finished_at"] = time.strftime("%Y%m%d_%H%M%S")

    (output_dir / "summary.json").write_text(
        json.dumps(run_meta, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "by_concept.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"Saved results to {output_dir}")
    return 0


if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()
    raise SystemExit(main())
