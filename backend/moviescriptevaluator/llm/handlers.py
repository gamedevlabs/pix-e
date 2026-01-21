from typing import Any, Dict

from llm import BaseOperationHandler, InvalidRequestError
from moviescriptevaluator.llm.prompts import AnalyzeScenePrompt, AnalyzeSceneWithAssetListPrompt
from moviescriptevaluator.llm.schemas import MovieScriptAnalysis, RecommendationResult


class AnalyzeScene(BaseOperationHandler):
    operation_id = "movie-script-evaluator.analyze"
    version = "1.0.0"
    description = "Evaluate scene using movie script"
    response_schema = MovieScriptAnalysis

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return AnalyzeScenePrompt % (data["scene_description"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "scene_description" not in data:
            raise InvalidRequestError("Scene description or elements missing")

class CreateRecommendation(BaseOperationHandler):
    operation_id = "movie-script-evaluator.create_recommendations"
    version = "1.0.0"
    description = "Create recommendation using asset list and needed assets"
    response_schema = RecommendationResult

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return AnalyzeSceneWithAssetListPrompt % (data["items_needed"] , data["asset_list"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "items_needed" not in data and "asset_list" not in data:
            raise InvalidRequestError("Required items or assets missing")

