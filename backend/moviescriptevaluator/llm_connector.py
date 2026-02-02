from typing import Any

# Import handlers to trigger auto-registration
from backend.moviescriptevaluator.llm import handlers  # noqa: F401
from llm import LLMOrchestrator, LLMRequest
from moviescriptevaluator.llm.schemas import RecommendationResult, RecommendationResultItem, MovieScriptAnalysis
from moviescriptevaluator.models import AssetMetaData, MovieScript, ScriptSceneAnalysisResult, RequiredAssets


class MovieScriptLLMConnector:
    orchestrator: LLMOrchestrator

    def __init__(self):
        self.orchestrator = LLMOrchestrator()

    def analyze_movie_script(
        self, movie_script: MovieScript
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

    def create_recommendations(self, items_needed: list[ScriptSceneAnalysisResult], asset_list: list[AssetMetaData]) -> RecommendationResult:
        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="create_recommendations",
            data={"items_needed": items_needed, "asset_list": asset_list},
            model_id="gemma3:4b",
            mode="monolithic",
            model_preference="local",
            temperature=None,
            max_tokens=None,
            provider_options=None,
        )

        response = self.orchestrator.execute(request)
        return RecommendationResult(**response.results)

    def analyze_missing_items(self, items_needed: list[ScriptSceneAnalysisResult], recommended_items: list[RequiredAssets]) -> MovieScriptAnalysis:
        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="missing_assets",
            data={"items_needed": items_needed, "recommended_items": recommended_items},
            model_id="gemma3:4b",
            mode="monolithic",
            model_preference="local",
            temperature=None,
            max_tokens=None,
            provider_options=None,
        )

        response = self.orchestrator.execute(request)
        return MovieScriptAnalysis(**response.results)
