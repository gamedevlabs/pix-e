from datetime import datetime
from typing import Any

# Import handlers to trigger auto-registration
from backend.moviescriptevaluator.llm import handlers  # noqa: F401
from llm import LLMOrchestrator, LLMRequest, LLMResponse
from moviescriptevaluator.llm.schemas import RecommendationResult, RecommendationResultItem, MovieScriptAnalysis
from moviescriptevaluator.models import AssetMetaData, MovieScript, ScriptSceneAnalysisResult, RequiredAssets

class Logger:
    log_file_path: str
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path

    def write_start_action(self):
        self.write_log("----------------------------Start of an action----------------------------")

    def write_end_action(self):
        self.write_log("----------------------------End of an action-----------------------------")

    def get_response_log(self, response: LLMResponse):
        return "models_used: {}, execution_time_in_ms: {}, token_usage: {}, operation_schema: {}".format(response.metadata.models_used, response.metadata.execution_time_ms, response.metadata.token_usage, response.metadata.operation_schema)

    def write_llm_response_log(self, response: LLMResponse):
        self.write_log(self.get_response_log(response))
        self.write_log("The operation is successful!!!")

    def write_log(self, message: str):
        time_stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open(self.log_file_path, 'a') as file:
            file.write(f"{time_stamp}: {message}\n")


class MovieScriptLLMConnector:
    orchestrator: LLMOrchestrator
    model_id: str

    def __init__(self, model_id: str):
        self.orchestrator = LLMOrchestrator()
        self.model_id = model_id
        self.logger = Logger("./moviescriptevaluator/logs/{}-{}.txt".format(self.model_id, datetime.today().strftime('%d-%m-%Y')))

    def set_model_id(self, model_id: str):
        self.model_id = model_id
        self.logger = Logger("./moviescriptevaluator/logs/{}-{}.txt".format(self.model_id, datetime.today().strftime('%d-%m-%Y')))

    def analyze_movie_script(
        self, movie_script: MovieScript
    ) -> dict[str, Any]:
        with movie_script.file.file.open("r") as movie_script_file:
            content = movie_script_file.read()

            self.logger.write_log("The LLM request is being triggered -> {} : {}".format("movie-script-evaluator", "analyze"))
            self.logger.write_log("The script to be analyzed: {}, length of the script: {}".format(movie_script.title, len(content)))

            request = LLMRequest(
                feature="movie-script-evaluator",
                operation="analyze",
                data={"scene_description": str(content)},
                model_id=self.model_id,
            )

            try:
                response = self.orchestrator.execute(request)
                self.logger.write_llm_response_log(response)
                return response.results
            except Exception as e:

                error_log = "Exception raised: ".format(e.message)
                self.logger.write_log(error_log)
                self.logger.write_log("The operation failed")

                return e


    def create_recommendations(self, items_needed: list[ScriptSceneAnalysisResult], asset_list: list[AssetMetaData]) -> RecommendationResult:

        self.logger.write_log("The LLM request is being triggered -> {} : {}".format("movie-script-evaluator", "create_recommendations"))
        self.logger.write_log(
            "The number of items passed: items_needed: {}, asset_list: {}, total: {}".format(len(items_needed),
                                                                                             len(asset_list),
                                                                                             len(items_needed) + len(
                                                                                                 asset_list)))


        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="create_recommendations",
            data={"items_needed": items_needed, "asset_list": asset_list},
            model_id=self.model_id,
        )

        try:
            response = self.orchestrator.execute(request)
            results = RecommendationResult(**response.results)

            self.logger.write_llm_response_log(response)
            self.logger.write_log("Number of recommendations: {}".format(len(results.result)))

            return results
        except Exception as e:

            error_log = "Exception raised: ".format(e.message)
            self.logger.write_log(error_log)
            self.logger.write_log("The operation failed")

            return e


    def analyze_missing_items(self, items_needed: list[ScriptSceneAnalysisResult], recommended_items: list[RequiredAssets]) -> MovieScriptAnalysis:
        self.logger.write_log(
            "The LLM request is being triggered -> {} : {}".format("movie-script-evaluator", "missing_assets"))
        self.logger.write_log(
            "The number of items passed: items_needed: {}, recommended_items: {}, total: {}".format(len(items_needed),
                                                                                             len(recommended_items),
                                                                                             len(items_needed) + len(
                                                                                                 recommended_items)))

        request = LLMRequest(
            feature="movie-script-evaluator",
            operation="missing_assets",
            data={"items_needed": items_needed, "recommended_items": recommended_items},
            model_id=self.model_id,
        )

        try:
            response = self.orchestrator.execute(request)
            results = MovieScriptAnalysis(**response.results)

            self.logger.write_llm_response_log(response)
            self.logger.write_log("Number of missing items: {}".format(len(results.result)))

            return results
        except Exception as e:

            error_log = "Exception raised: ".format(e.message)
            self.logger.write_log(error_log)
            self.logger.write_log("The operation failed")

            return e
