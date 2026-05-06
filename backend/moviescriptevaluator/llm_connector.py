from typing import Any

from llm import LLMOrchestrator, LLMRequest

# Import handlers to trigger auto-registration
from moviescriptevaluator.llm import handlers  # noqa: F401
from moviescriptevaluator.models import AssetMetaData, MovieScript


class MovieScriptLLMConnector:
    """LLM connector for movie script analysis.

    Uses a per-user orchestrator (passed in at construction) instead of
    the old global env-var pattern, so each user's stored API keys are used.
    """

    def __init__(self, orchestrator: LLMOrchestrator):
        self.orchestrator = orchestrator

    def analyze_movie_script(
        self, movie_script: MovieScript, asset_list: list[AssetMetaData]
    ) -> dict[str, Any]:
        with movie_script.file.file.open("r") as movie_script_file:
            content = movie_script_file.read()

            request = LLMRequest(
                feature="movie-script-evaluator",
                operation="analyze",
                data={"scene_description": str(content)},
                model_id="gemma3:4b",
                mode="monolithic",
                model_preference="local",
                temperature=None,
                max_tokens=None,
                provider_options=None,
            )

            response = self.orchestrator.execute(request)
            return response.results
