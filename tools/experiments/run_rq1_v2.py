"""
RQ1 V2 Experiment Runner -- Three-arm comparison with unified output schema.

Changes from run_rq1.py:
- Uses MonolithicRQ1Handler (operation sparc.monolithic_rq1) producing
  per-aspect + synthesis in a single structured call
- Sets pillar_mode="none" for ALL three arms (removes pillar confound)
- Eliminates all normalization LLM calls
- Validates outputs against RQ1UnifiedResponse schema
- Tracks per-arm token counts, LLM call counts, and cost
- Logfire spans for observability

Usage:
    python tools/experiments/run_rq1_v2.py --user-id 2 --model gpt-4o-mini
    python tools/experiments/run_rq1_v2.py --user-id 2 --model gpt-4o-mini --project-id 75
"""

import argparse
import json
import os
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import django


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_id_spec(spec: str) -> List[int]:
    """Parse '78,79,80-92' into a flat list of ints."""
    ids: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            ids.extend(range(int(lo), int(hi) + 1))
        else:
            ids.append(int(part))
    return ids



def _resolve_concept(project: Any) -> Optional[Any]:
    """Find the current GameConcept for a project (or most recent)."""
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


def _validate_unified_response(data: Dict[str, Any]) -> List[str]:
    """
    Validate that a dict conforms to RQ1UnifiedResponse.

    Returns a list of validation error strings (empty = valid).
    """
    from sparc.llm.schemas.rq1 import SPARC_ASPECT_NAMES, RQ1UnifiedResponse

    errors: List[str] = []

    try:
        parsed = RQ1UnifiedResponse.model_validate(data)
    except Exception as exc:
        return [f"Schema validation failed: {exc}"]

    # Check all 10 aspects are present
    missing = set(SPARC_ASPECT_NAMES) - set(parsed.aspect_results.keys())
    if missing:
        errors.append(f"Missing aspects: {sorted(missing)}")

    # Check status values are valid
    valid_statuses = {"well_defined", "needs_work", "not_provided"}
    for name, aspect in parsed.aspect_results.items():
        if aspect.status not in valid_statuses:
            errors.append(f"Invalid status '{aspect.status}' for aspect '{name}'")

    valid_overall = {"ready", "nearly_ready", "needs_work"}
    if parsed.synthesis.overall_status not in valid_overall:
        errors.append(
            f"Invalid overall_status: '{parsed.synthesis.overall_status}'"
        )

    return errors


# ---------------------------------------------------------------------------
# Arm 1: Monolithic
# ---------------------------------------------------------------------------

def _run_monolithic_rq1(
    game_text: str,
    model_id: str,
    logfire: Any,
) -> Dict[str, Any]:
    """Single LLM call producing RQ1UnifiedResponse."""
    from llm.cost_tracking import calculate_cost_eur
    from llm.orchestrator import LLMOrchestrator
    from llm.types import LLMRequest

    orchestrator = LLMOrchestrator()
    request = LLMRequest(
        feature="sparc",
        operation="monolithic_rq1",
        data={"game_text": game_text},
        mode="monolithic",
        model_id=model_id,
    )

    start = time.time()
    response = orchestrator.execute(request)
    elapsed_ms = int((time.time() - start) * 1000)

    token_usage = response.metadata.token_usage
    prompt_tokens = token_usage.prompt_tokens if token_usage else 0
    completion_tokens = token_usage.completion_tokens if token_usage else 0
    total_tokens = token_usage.total_tokens if token_usage else 0
    cost = float(calculate_cost_eur(model_id, prompt_tokens, completion_tokens))

    result: Dict[str, Any] = {
        "success": response.success,
        "response": None,
        "execution_time_ms": elapsed_ms,
        "total_tokens": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "llm_calls": 1,
        "estimated_cost_eur": cost,
        "errors": [],
        "validation_errors": [],
    }

    if not response.success:
        result["errors"] = [
            e.message for e in response.errors
        ] if response.errors else ["Unknown error"]
        logfire.warning(
            "Monolithic call failed: {errors}",
            errors=result["errors"],
        )
        return result

    # Validate the output
    validation_errors = _validate_unified_response(response.results)
    if validation_errors:
        logfire.warning(
            "Monolithic validation warnings: {validation_errors}",
            validation_errors=validation_errors,
            model=model_id,
        )
        result["validation_errors"] = validation_errors

    result["response"] = response.results
    logfire.info(
        "Monolithic done — {total_tokens} tokens, {execution_time_ms}ms, "
        "EUR {cost_eur:.6f}",
        total_tokens=total_tokens,
        execution_time_ms=elapsed_ms,
        cost_eur=cost,
        validation_errors_count=len(validation_errors),
    )
    return result


# ---------------------------------------------------------------------------
# Arms 2 & 3: Agentic
# ---------------------------------------------------------------------------

def _run_agentic(
    *,
    game_text: str,
    model_id: str,
    user: Any,
    context_strategy: str,
    project_id: Optional[int],
    logfire: Any,
) -> Dict[str, Any]:
    """Parallel agents + synthesis, returning RQ1UnifiedResponse shape."""
    import asyncio

    from llm.config import get_config
    from llm.cost_tracking import calculate_cost_eur
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
        "pillar_mode": "none",
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

    start = time.time()
    exec_result = asyncio.run(workflow.run(request, mode="full"))
    elapsed_ms = int((time.time() - start) * 1000)

    # Sum tokens from individual agent results (authoritative source)
    total_prompt = sum(r.prompt_tokens for r in exec_result.agent_results)
    total_completion = sum(r.completion_tokens for r in exec_result.agent_results)
    total_tokens = sum(r.total_tokens for r in exec_result.agent_results)

    # Count real LLM calls (exclude zero-token no-ops like empty pillar agent)
    llm_calls = sum(
        1 for r in exec_result.agent_results if r.total_tokens > 0
    )

    cost = float(calculate_cost_eur(model_id, total_prompt, total_completion))

    result: Dict[str, Any] = {
        "success": exec_result.success,
        "response": None,
        "execution_time_ms": elapsed_ms,
        "total_tokens": total_tokens,
        "prompt_tokens": total_prompt,
        "completion_tokens": total_completion,
        "llm_calls": llm_calls,
        "estimated_cost_eur": cost,
        "errors": [],
        "validation_errors": [],
    }

    if not exec_result.success:
        result["errors"] = [
            e.message for e in exec_result.errors
        ] if exec_result.errors else ["Unknown error"]
        logfire.warning(
            "Agentic {context_strategy} failed: {errors}",
            context_strategy=context_strategy,
            errors=result["errors"],
        )
        return result

    # Extract unified response from SPARCV2Response
    agg = exec_result.aggregated_data
    aspect_results = agg.get("aspect_results", {})
    synthesis = agg.get("synthesis")

    if aspect_results and synthesis:
        unified = {
            "aspect_results": aspect_results,
            "synthesis": synthesis,
        }
        validation_errors = _validate_unified_response(unified)
        if validation_errors:
            logfire.warning(
                "Agentic {context_strategy} validation warnings: "
                "{validation_errors}",
                context_strategy=context_strategy,
                validation_errors=validation_errors,
            )
            result["validation_errors"] = validation_errors
        result["response"] = unified
    else:
        missing_parts = []
        if not aspect_results:
            missing_parts.append("aspect_results")
        if not synthesis:
            missing_parts.append("synthesis")
        result["errors"].append(
            f"Agentic output missing: {', '.join(missing_parts)}"
        )
        logfire.warning(
            "Agentic {context_strategy} incomplete — missing: {missing_parts}",
            context_strategy=context_strategy,
            missing_parts=missing_parts,
        )

    logfire.info(
        "Agentic {context_strategy} done — {total_tokens} tokens, "
        "{llm_calls} LLM calls, {execution_time_ms}ms, EUR {cost_eur:.6f}",
        context_strategy=context_strategy,
        total_tokens=total_tokens,
        llm_calls=llm_calls,
        execution_time_ms=elapsed_ms,
        cost_eur=cost,
        validation_errors_count=len(result.get("validation_errors", [])),
    )
    return result


# ---------------------------------------------------------------------------
# Per-concept evaluation
# ---------------------------------------------------------------------------

def _build_failed_result(error: Exception) -> Dict[str, Any]:
    return {
        "success": False,
        "response": None,
        "execution_time_ms": 0,
        "total_tokens": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "llm_calls": 0,
        "estimated_cost_eur": 0.0,
        "errors": [str(error)],
        "validation_errors": [],
    }


def _evaluate_concept(
    *,
    concept_payload: Dict[str, Any],
    user_id: int,
    model_name: str,
) -> Dict[str, Any]:
    """Evaluate a single concept across all three modes (sequentially)."""
    from django.contrib.auth import get_user_model

    from llm.logfire_config import get_logfire

    logfire = get_logfire()
    user = get_user_model().objects.get(id=user_id)

    game_text = concept_payload["game_text"]
    project_id = concept_payload["project_id"]
    project_name = concept_payload["project_name"]
    concept_id = concept_payload["concept_id"]

    with logfire.span(
        "Evaluate concept: {project_name}",
        project_id=str(project_id),
        project_name=project_name,
        concept_id=str(concept_id),
        game_text_length=len(game_text),
    ):
        # Arm 1: Monolithic
        with logfire.span(
            "Arm 1 — Monolithic ({model})",
            model=model_name,
        ):
            try:
                monolithic = _run_monolithic_rq1(
                    game_text, model_name, logfire
                )
            except Exception as exc:
                logfire.exception("Monolithic evaluation failed", error=str(exc))
                monolithic = _build_failed_result(exc)

        # Arm 2: Agentic full-text
        with logfire.span(
            "Arm 2 — Agentic full-text ({model})",
            model=model_name,
            context_strategy="full_text",
        ):
            try:
                agentic_full = _run_agentic(
                    game_text=game_text,
                    model_id=model_name,
                    user=user,
                    context_strategy="full_text",
                    project_id=project_id,
                    logfire=logfire,
                )
            except Exception as exc:
                logfire.exception(
                    "Agentic full-text evaluation failed", error=str(exc)
                )
                agentic_full = _build_failed_result(exc)

        # Arm 3: Agentic routed
        with logfire.span(
            "Arm 3 — Agentic routed ({model})",
            model=model_name,
            context_strategy="router",
        ):
            try:
                agentic_routed = _run_agentic(
                    game_text=game_text,
                    model_id=model_name,
                    user=user,
                    context_strategy="router",
                    project_id=project_id,
                    logfire=logfire,
                )
            except Exception as exc:
                logfire.exception(
                    "Agentic routed evaluation failed", error=str(exc)
                )
                agentic_routed = _build_failed_result(exc)

        # Summary logging for this concept
        logfire.info(
            "Concept done: {project_name} — mono={monolithic_tokens}t, "
            "full={agentic_full_text_tokens}t, routed={agentic_routed_tokens}t",
            project_name=project_name,
            monolithic_success=monolithic["success"],
            agentic_full_text_success=agentic_full["success"],
            agentic_routed_success=agentic_routed["success"],
            monolithic_tokens=monolithic["total_tokens"],
            agentic_full_text_tokens=agentic_full["total_tokens"],
            agentic_routed_tokens=agentic_routed["total_tokens"],
        )

    return {
        "project_id": project_id,
        "project_name": project_name,
        "concept_id": concept_id,
        "game_text": game_text,
        "game_text_length": len(game_text),
        "monolithic": monolithic,
        "agentic_full_text": agentic_full,
        "agentic_routed": agentic_routed,
        "_index": concept_payload["_index"],
    }


# ---------------------------------------------------------------------------
# JSON serializer for Decimal
# ---------------------------------------------------------------------------

def _print_concept_result(result: Dict[str, Any]) -> None:
    """Print per-concept arm summary."""
    for arm in ("monolithic", "agentic_full_text", "agentic_routed"):
        arm_data = result[arm]
        status = "OK" if arm_data["success"] else "FAIL"
        tokens = arm_data["total_tokens"]
        ms = arm_data["execution_time_ms"]
        ve = len(arm_data.get("validation_errors", []))
        ve_str = f" ({ve} validation warnings)" if ve else ""
        print(f"    {arm}: {status} | {tokens} tokens | {ms}ms{ve_str}")


class _DecimalEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="RQ1 V2: Three-arm SPARC evaluation with unified output schema"
    )
    parser.add_argument("--user-id", type=int, default=2)
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of concepts processed.",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="Run for a single project id.",
    )
    parser.add_argument(
        "--project-ids",
        type=str,
        default=None,
        help="Comma-separated project IDs and/or ranges (e.g., '78-92,93-107').",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=1,
        help="Max concepts to evaluate in parallel (default: 1).",
    )

    args = parser.parse_args()

    from django.contrib.auth import get_user_model

    from game_concept.models import Project
    from llm.logfire_config import get_logfire

    user_model = get_user_model()
    try:
        user = user_model.objects.get(id=args.user_id)
    except user_model.DoesNotExist as exc:
        raise SystemExit(f"User not found: {args.user_id}") from exc

    projects = Project.objects.filter(user=user).order_by("id")
    if args.project_id:
        projects = projects.filter(id=args.project_id)
    if args.project_ids:
        projects = projects.filter(id__in=_parse_id_spec(args.project_ids))
    if args.limit is not None:
        projects = projects[: max(0, args.limit)]

    if not projects:
        raise SystemExit("No projects found for the requested scope.")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir or f"docs/experiments/rq1_v2_run_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)

    logfire = get_logfire()

    run_meta = {
        "user_id": args.user_id,
        "model": args.model,
        "temperature": 0,
        "pillar_mode": "none",
        "project_id": args.project_id,
        "project_ids": args.project_ids,
        "max_parallel": args.max_parallel,
        "limit": args.limit,
        "started_at": timestamp,
    }

    # Build concept payloads
    concept_payloads: List[Dict[str, Any]] = []
    for index, project in enumerate(projects):
        concept = _resolve_concept(project)
        if not concept:
            logfire.warning(
                "Skipping project {project_name} — no concept found",
                project_id=str(project.id),
                project_name=project.name,
                reason="no_concept_found",
            )
            continue
        concept_payloads.append(
            {
                "project_id": project.id,
                "project_name": project.name,
                "concept_id": concept.id,
                "game_text": concept.content,
                "_index": index,
            }
        )

    total_concepts = len(concept_payloads)
    print(
        f"Running RQ1 V2 experiment: {total_concepts} concepts, "
        f"model={args.model}, pillar_mode=none"
    )

    results: List[Dict[str, Any]] = []

    max_parallel = max(1, args.max_parallel)

    with logfire.span(
        "RQ1 V2 experiment — {total_concepts} concepts, model={model}, "
        "parallel={max_parallel}",
        user_id=args.user_id,
        model=args.model,
        total_concepts=total_concepts,
        max_parallel=max_parallel,
        project_id=str(args.project_id or ""),
        project_ids=args.project_ids or "",
    ):
        if max_parallel == 1:
            # Sequential execution
            for i, payload in enumerate(concept_payloads):
                print(
                    f"  [{i + 1}/{total_concepts}] {payload['project_name']} "
                    f"(project_id={payload['project_id']})"
                )
                try:
                    result = _evaluate_concept(
                        concept_payload=payload,
                        user_id=args.user_id,
                        model_name=args.model,
                    )
                    results.append(result)
                    _print_concept_result(result)
                except Exception as exc:
                    logfire.exception(
                        "Fatal error evaluating project {project_id}: {error}",
                        project_id=str(payload["project_id"]),
                        error=str(exc),
                    )
                    print(f"    FATAL ERROR: {exc}")
        else:
            # Parallel execution with ThreadPoolExecutor
            from concurrent.futures import ThreadPoolExecutor, as_completed

            futures = {}
            with ThreadPoolExecutor(max_workers=max_parallel) as executor:
                for i, payload in enumerate(concept_payloads):
                    print(
                        f"  [{i + 1}/{total_concepts}] Queued: "
                        f"{payload['project_name']} "
                        f"(project_id={payload['project_id']})"
                    )
                    future = executor.submit(
                        _evaluate_concept,
                        concept_payload=payload,
                        user_id=args.user_id,
                        model_name=args.model,
                    )
                    futures[future] = payload

                for future in as_completed(futures):
                    payload = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        print(f"  Done: {payload['project_name']}")
                        _print_concept_result(result)
                    except Exception as exc:
                        logfire.exception(
                            "Fatal error evaluating project {project_id}: "
                            "{error}",
                            project_id=str(payload["project_id"]),
                            error=str(exc),
                        )
                        print(
                            f"  FATAL ERROR: {payload['project_name']}: {exc}"
                        )

    run_meta["finished_at"] = time.strftime("%Y%m%d_%H%M%S")
    run_meta["total_concepts"] = len(results)

    # Compute run-level totals
    total_cost = 0.0
    total_tokens_all = 0
    for r in results:
        for arm in ("monolithic", "agentic_full_text", "agentic_routed"):
            total_cost += r[arm].get("estimated_cost_eur", 0.0)
            total_tokens_all += r[arm].get("total_tokens", 0)
    run_meta["total_cost_eur"] = round(total_cost, 8)
    run_meta["total_tokens"] = total_tokens_all

    # Sort by original index, then remove internal _index field
    results.sort(key=lambda item: item.get("_index", 0))
    for item in results:
        item.pop("_index", None)

    # Write output
    (output_dir / "summary.json").write_text(
        json.dumps(run_meta, indent=2, cls=_DecimalEncoder) + "\n",
        encoding="utf-8",
    )
    (output_dir / "by_concept.json").write_text(
        json.dumps(results, indent=2, cls=_DecimalEncoder) + "\n",
        encoding="utf-8",
    )

    print(f"\nResults saved to {output_dir}/")
    print(f"Total cost: EUR {total_cost:.6f} | Total tokens: {total_tokens_all}")

    # Report validation summary
    v_warn_count = 0
    for r in results:
        for arm in ("monolithic", "agentic_full_text", "agentic_routed"):
            v_warn_count += len(r[arm].get("validation_errors", []))
    if v_warn_count:
        print(f"WARNING: {v_warn_count} validation warnings across all runs")

    # Flush all pending logfire spans before exit
    try:
        logfire.shutdown()
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parents[2] / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.settings")
    django.setup()
    raise SystemExit(main())
