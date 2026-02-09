from abc import ABC, abstractmethod
from datetime import datetime

from llm import LLMResponse


class Logger(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def write_start_action(self):
        pass

    @abstractmethod
    def write_end_action(self):
        pass

    @abstractmethod
    def get_response_log(self, response: LLMResponse):
        pass

    @abstractmethod
    def write_llm_response_log(self, response: LLMResponse):
        pass

    @abstractmethod
    def write_log(self, message: str):
        pass


class PassiveLogger(Logger):

    def write_start_action(self):
        pass

    def write_end_action(self):
        pass

    def get_response_log(self, response: LLMResponse):
        pass

    def write_llm_response_log(self, response: LLMResponse):
        pass

    def write_log(self, message: str):
        pass


class ActiveLogger(Logger):
    log_file_path: str

    def __init__(self, log_file_path: str):
        super().__init__()
        self.log_file_path: str = log_file_path

    def write_start_action(self):
        self.write_log(
            "----------------------------Start of an action----------------------------"
        )

    def write_end_action(self):
        self.write_log(
            "----------------------------End of an action-----------------------------"
        )

    def get_response_log(self, response: LLMResponse):
        return (
            "models_used: {}, execution_time_in_ms: {}, "
            "token_usage: {}, operation_schema: {}"
        ).format(
            response.metadata.models_used,
            response.metadata.execution_time_ms,
            response.metadata.token_usage,
            response.metadata.operation_schema,
        )

    def write_llm_response_log(self, response: LLMResponse):
        self.write_log(self.get_response_log(response))
        self.write_log("The operation is successful!!!")

    def write_log(self, message: str):
        time_stamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open(self.log_file_path, "a") as file:
            file.write(f"{time_stamp}: {message}\n")
