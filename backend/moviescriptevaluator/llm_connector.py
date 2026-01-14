from typing import Any

# Import handlers to trigger auto-registration
from backend.moviescriptevaluator.llm import handlers  # noqa: F401
from llm import LLMOrchestrator, LLMRequest
from moviescriptevaluator.models import AssetMetaData, MovieScript


class MovieScriptLLMConnector:
    orchestrator: LLMOrchestrator

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

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
