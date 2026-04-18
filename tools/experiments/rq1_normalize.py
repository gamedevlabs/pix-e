from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError

from llm.orchestrator import LLMOrchestrator
from llm.types import LLMRequest
from tools.experiments.rq1_synthesis import RQ1Synthesis


def run_rq1_normalize(
    *,
    model_name: str,
    evaluation_output: Dict[str, Any],
    evaluation_type: str,
) -> Dict[str, Any]:
    if not evaluation_output:
        return {}

    orchestrator = LLMOrchestrator()
    request = LLMRequest(
        feature="sparc",
        operation="rq1_normalize",
        data={
            "evaluation_output": evaluation_output,
            "evaluation_type": evaluation_type,
        },
        mode="monolithic",
        model_id=model_name,
    )
    response = orchestrator.execute(request)
    if not response.success or not response.results:
        return {}

    try:
        return RQ1Synthesis(**response.results).model_dump()
    except ValidationError:
        return response.results
