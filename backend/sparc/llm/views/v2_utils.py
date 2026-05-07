"""
Shared helpers for SPARC v2 views.
"""

import asyncio
import tempfile
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.request import Request

from game_concept.models import Project
from game_concept.utils import get_current_game_concept, get_current_project
from llm.config import get_config
from llm.events import EventCollector
from llm.providers.manager import ModelManager
from llm.types import LLMRequest
from sparc.llm.utils.file_extraction import validate_file_size, validate_file_type
from sparc.llm.workflows_v2 import SPARCRouterWorkflow
from sparc.models import SPARCEvaluation

VALID_PILLAR_MODES = {"all", "smart", "none"}


def get_model_id(model_name: str) -> str:
    config = get_config()
    return config.resolve_model_alias(model_name)


def resolve_concept_meta(request: Request) -> dict[str, str]:
    project = None
    project_id = request.data.get("project_id")
    if project_id:
        project = Project.objects.filter(id=project_id).first()
    elif request.user.is_authenticated:
        project = get_current_project(request.user)
    concept = get_current_game_concept(project) if project else None
    concept_text = (concept.content or "") if concept else ""
    preview = (
        concept_text[:80] + "..."
        if concept_text and len(concept_text) > 80
        else concept_text
    )
    return {
        "project_id": str(getattr(project, "id", "")) if project else "",
        "project_name": getattr(project, "name", "") if project else "",
        "concept_name": getattr(project, "name", "") if project else "",
        "concept_preview": preview,
    }


def build_request_data(
    *,
    game_text: str,
    context_text: str,
    pillar_mode: str,
    project_id: Optional[int] = None,
    context_strategy: Optional[str] = None,
    document_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    request_data: Dict[str, Any] = {
        "game_text": game_text,
        "context": context_text,
        "pillar_mode": pillar_mode,
    }
    if project_id:
        request_data["project_id"] = project_id
    if context_strategy:
        request_data["context_strategy"] = context_strategy
    if document_data:
        request_data["document_file"] = document_data
    return request_data


def create_evaluation(
    *,
    game_text: str,
    context_text: str,
    mode: str,
    pillar_mode: str,
    model_id: str,
) -> SPARCEvaluation:
    return SPARCEvaluation.objects.create(
        game_text=game_text,
        context=context_text,
        mode=mode,
        pillar_mode=pillar_mode,
        model_id=model_id,
        execution_time_ms=0,
        total_tokens=0,
        estimated_cost_eur=0,
    )


def update_evaluation_totals(
    evaluation: SPARCEvaluation, aggregated: Dict[str, Any]
) -> None:
    evaluation.execution_time_ms = aggregated.get("execution_time_ms", 0)
    evaluation.total_tokens = aggregated.get("total_tokens", 0)
    evaluation.estimated_cost_eur = aggregated.get("estimated_cost_eur", 0)
    evaluation.save()


def run_router_workflow(
    *,
    request_data: Dict[str, Any],
    model_id: str,
    evaluation: SPARCEvaluation,
    user: Optional[User],
    mode: str,
    target_aspects: Optional[list[str]] = None,
    event_collector: Optional[EventCollector] = None,
):
    config = get_config()
    model_manager = ModelManager(config)
    event_collector = event_collector or EventCollector()

    workflow = SPARCRouterWorkflow(
        model_manager=model_manager,
        config=config,
        event_collector=event_collector,
        evaluation=evaluation,
        user=user,
    )

    request = LLMRequest(
        feature="sparc",
        operation="router_v2",
        data=request_data,
        model_id=model_id,
        mode="agentic",
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            workflow.run(request, mode=mode, target_aspects=target_aspects)
        )
    finally:
        loop.close()


def save_uploaded_document(uploaded_file) -> tuple[Dict[str, Any], str]:
    file_type = validate_file_type(uploaded_file.name, settings.ALLOWED_DOCUMENT_TYPES)
    validate_file_size(uploaded_file.size, settings.DOCUMENT_MAX_SIZE_MB)
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{file_type}",
        dir=tempfile.gettempdir(),
    ) as tmp_file:
        for chunk in uploaded_file.chunks():
            tmp_file.write(chunk)
        temp_file_path = tmp_file.name
    return (
        {
            "file_path": temp_file_path,
            "file_type": file_type,
            "original_name": uploaded_file.name,
        },
        temp_file_path,
    )
