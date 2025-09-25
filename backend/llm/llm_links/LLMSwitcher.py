from llm.llm_links.GeminiLink import GeminiLink
from llm.llm_links.LLMLink import LLMLink
from llm.llm_links.OpenAILink import OpenAILink


class LLMSwitcher:
    """
    Manager class holding references to different LLMs.
    """

    def __init__(self):
        self.gemini = GeminiLink()
        self.openai = OpenAILink()

    def get_llm(self, model: str) -> LLMLink:
        match model:
            case "gemini":
                return self.gemini
            case "openai":
                return self.openai
            case _:
                raise ValueError(f"Unsupported model: {model}")
