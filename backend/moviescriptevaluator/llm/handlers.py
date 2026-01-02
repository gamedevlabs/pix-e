from typing import Any, Dict

from llm import BaseOperationHandler, InvalidRequestError
from moviescriptevaluator.llm.prompts import AnalyzeScenePrompt
from moviescriptevaluator.llm.schemas import AssetListAnalysis


class AnalyzeScene(BaseOperationHandler):
    operation_id = "movie-script-evaluator.analyze"
    version = "1.0.0"
    description = "Evaluate scene using movie script"
    response_schema = AssetListAnalysis

    def build_prompt(self, data: Dict[str, Any]) -> str:
        return AnalyzeScenePrompt % (data["scene_description"], data["elements"])

    def validate_input(self, data: Dict[str, Any]) -> None:
        if "scene_description" not in data or "elements" not in data:
            raise InvalidRequestError("Scene description or elements missing")
