from datetime import datetime
from typing import Any

# Import handlers to trigger auto-registration
from backend.moviescriptevaluator.llm import handlers  # noqa: F401
from llm import LLMOrchestrator, LLMRequest
from moviescriptevaluator.config import get_config_mse
from moviescriptevaluator.llm.schemas import (
    MovieScriptAnalysis,
    RecommendationResult,
)
from moviescriptevaluator.logger import ActiveLogger, Logger, PassiveLogger
from moviescriptevaluator.models import (
    AssetMetaData,
    MovieScript,
    RequiredAssets,
    ScriptSceneAnalysisResult,
)


class MovieScriptLLMConnector:
    orchestrator: LLMOrchestrator
    model_id: str
    logger: Logger

    def __init__(self, model_id: str):
        self.orchestrator = LLMOrchestrator()
        self.model_id = model_id

        config = get_config_mse()

        if config.is_logging_enabled:
            self.logger = ActiveLogger(
                config.logging_directory.format(
                    self.model_id, datetime.today().strftime("%d-%m-%Y")
                )
            )
        else:
            self.logger = PassiveLogger()

    def set_model_id(self, model_id: str):
        self.model_id = model_id

        config = get_config_mse()

        if config.is_logging_enabled:
            self.logger = ActiveLogger(
                config.logging_directory.format(
                    self.model_id, datetime.today().strftime("%d-%m-%Y")
                )
            )
        else:
            self.logger = PassiveLogger()

    def analyze_movie_script(self, movie_script: MovieScript) -> dict[str, Any]:
        with movie_script.file.file.open("r") as movie_script_file:
            content = movie_script_file.read()

            self.logger.write_log(
                "The LLM request is being triggered -> {} : {}".format(
                    "movie-script-evaluator", "analyze"
                )
            )
            self.logger.write_log(
                "The script to be analyzed: {}, length of the script: {}".format(
                    movie_script.title, len(content)
                )
            )

            request = LLMRequest(
                feature="movie-script-evaluator",
                operation="analyze",
                data={"scene_description": str(content)},
                model_id=self.model_id,
                mode="monolithic",
                model_preference="auto",
                temperature=0.7,
                max_tokens=None,
                provider_options=None,
            )

            try:
                response = self.orchestrator.execute(request)
                self.logger.write_llm_response_log(response)
                return response.results
            except Exception as e:

                # Log and rethrow the exception
                error_log = "Exception raised: {}".format(e)
                self.logger.write_log(error_log)
                self.logger.write_log("The operation failed")

                raise e

    def create_recommendations(
        self,
        items_needed: list[ScriptSceneAnalysisResult],
        asset_list: list[AssetMetaData],
    ) -> RecommendationResult:

        self.logger.write_log(
            "The LLM request is being triggered -> {} : {}".format(
                "movie-script-evaluator", "create_recommendations"
            )
        )
        self.logger.write_log(
            (
                "The number of items passed: items_needed: {}, "
                "asset_list: {}, total: {}"
            ).format(
                len(items_needed), len(asset_list), len(items_needed) + len(asset_list)
            )
        )

        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="create_recommendations",
            data={"items_needed": items_needed, "asset_list": asset_list},
            model_id=self.model_id,
            mode="monolithic",
            model_preference="auto",
            temperature=0.7,
            max_tokens=None,
            provider_options=None,
        )

        try:
            response = self.orchestrator.execute(request)
            results = RecommendationResult(**response.results)

            self.logger.write_llm_response_log(response)
            self.logger.write_log(
                "Number of recommendations: {}".format(len(results.result))
            )

            return results
        except Exception as e:
            # Log and rethrow the exception
            error_log = "Exception raised: {}".format(e)
            self.logger.write_log(error_log)
            self.logger.write_log("The operation failed")

            raise e

    def analyze_missing_items(
        self,
        items_needed: list[ScriptSceneAnalysisResult],
        recommended_items: list[RequiredAssets],
    ) -> MovieScriptAnalysis:
        self.logger.write_log(
            "The LLM request is being triggered -> {} : {}".format(
                "movie-script-evaluator", "missing_assets"
            )
        )
        self.logger.write_log(
            (
                "The number of items: items_needed: {}, "
                "recommended_items: {}, total: {}"
            ).format(
                len(items_needed),
                len(recommended_items),
                len(items_needed) + len(recommended_items),
            )
        )

        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="missing_assets",
            data={"items_needed": items_needed, "recommended_items": recommended_items},
            model_id=self.model_id,
            mode="monolithic",
            model_preference="auto",
            temperature=0.7,
            max_tokens=None,
            provider_options=None,
        )

        try:
            response = self.orchestrator.execute(request)
            results = MovieScriptAnalysis(**response.results)

            self.logger.write_llm_response_log(response)
            self.logger.write_log(
                "Number of missing items: {}".format(len(results.result))
            )

            return results
        except Exception as e:
            # Log and rethrow the exception
            error_log = "Exception raised: {}".format(e)
            self.logger.write_log(error_log)
            self.logger.write_log("The operation failed")

            raise e
