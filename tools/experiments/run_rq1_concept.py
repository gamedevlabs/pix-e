import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import django


def _load_django() -> None:
    backend_root = Path.cwd() / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()


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
    parser = argparse.ArgumentParser(
        description="Run RQ1 evaluation for a single concept."
    )
    parser.add_argument("--user-id", type=int, default=2)
    parser.add_argument("--concept-id", type=int, required=True)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    from django.contrib.auth import get_user_model
    from game_concept.models import GameConcept

    user = get_user_model().objects.get(id=args.user_id)
    concept = GameConcept.objects.get(id=args.concept_id)
    project = concept.project

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(
        args.output_dir
        or f"docs/experiments/rq1_concept_{args.concept_id}_{timestamp}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    game_text = concept.content

    monolithic = _run_monolithic(game_text, args.model)
    agentic_full = _run_router_v2(
        game_text=game_text,
        model_id=args.model,
        user=user,
        pillar_mode="none",
        context_strategy="full_text",
        project_id=project.id if project else None,
    )
    agentic_routed = _run_router_v2(
        game_text=game_text,
        model_id=args.model,
        user=user,
        pillar_mode="smart",
        context_strategy="router",
        project_id=project.id if project else None,
    )

    summary = {
        "user_id": args.user_id,
        "model": args.model,
        "project_id": project.id if project else None,
        "concept_id": concept.id,
        "started_at": timestamp,
        "finished_at": time.strftime("%Y%m%d_%H%M%S"),
    }
    by_concept = [
        {
            "project_id": project.id if project else None,
            "project_name": project.name if project else "",
            "project_description": project.description if project else "",
            "concept_id": concept.id,
            "game_text": game_text,
            "monolithic": monolithic,
            "agentic_full_text": agentic_full,
            "agentic_routed": agentic_routed,
        }
    ]

    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "by_concept.json").write_text(
        json.dumps(by_concept, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    print(f"Saved results to {output_dir}")
    return 0


if __name__ == "__main__":
    _load_django()
    raise SystemExit(main())
