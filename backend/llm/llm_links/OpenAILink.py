import os

from openai import OpenAI

from llm.llm_links import PillarPrompts
from llm.llm_links.LLMLink import LLMLink
from llm.llm_links.PillarPrompts import ValidationPrompt
from llm.llm_links.responseSchemes import PillarResponse, StringFeedback
from llm.models import Pillar


class OpenAILink(LLMLink):
    def __init__(self):
        key = os.environ.get("OPENAI_API_KEY")
        if key is None:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=key)  # could also auto infer from environment
        pass

    def evaluate_pillars_in_context(self, pillars: list[Pillar], context: str) -> StringFeedback:
        prompt = PillarPrompts.OverallFeedbackPrompt % (
            context,
            "\n".join(
                [f"{pillar.name}:\n {pillar.description}" for pillar in pillars]
            ),
        )
        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            text_format=StringFeedback,
        )
        return response.output_parsed

    def evaluate_pillar(self, pillar: Pillar) -> PillarResponse:
        """
        Generate a response for a game design pillar.
        :param pillar: The pillar text to analyze.
        :return: A PillarResponse object containing the analysis.
        """
        prompt = ValidationPrompt % (pillar.name, pillar.description)
        response = self.client.responses.parse(
            model="gpt-4o-mini",
            input=prompt,
            text_format=PillarResponse,
        )
        return response.output_parsed

    def improve_pillar(self, pillar: Pillar) -> Pillar:
        raise NotImplementedError()

    def evaluate_context_with_pillars(self, pillars: list[Pillar], context: str) -> StringFeedback:
        raise NotImplementedError()