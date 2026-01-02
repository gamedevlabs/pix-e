from typing import Any

from llm import LLMOrchestrator, LLMRequest
from moviescriptevaluator.models import AssetMetaData, MovieScript
# Import handlers to trigger auto-registration
from backend.moviescriptevaluator.llm import handlers  # noqa: F401


class MovieScriptLLMConnector:
    orchestrator: LLMOrchestrator
    
    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    def analyze_movie_script(self, movie_script: MovieScript, asset_list: list[AssetMetaData]) -> dict[str, Any]:
        with movie_script.file.file.open('r') as movie_script_file:
            content = movie_script_file.read()

            request = LLMRequest(
                feature="movie-script-evaluator",
                operation="analyze",
                data={"scene_description": str(content), "elements": asset_list.__str__()},
                model_id="deepseek-r1:8b",
                mode="monolithic",
                model_preference="local"
            )

            response = self.orchestrator.execute(request)
            return response.results



        
        