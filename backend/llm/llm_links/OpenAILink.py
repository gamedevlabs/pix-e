import os

from openai import OpenAI

from llm.llm_links.PillarPrompts import ValidationPrompt
from llm.llm_links.responseSchemes import PillarResponse
from llm.models import Pillar


class OpenAILink:

    def __init__(self):
        key = os.environ.get("OPENAI_API_KEY")
        if key is None:
            raise ValueError("GEMINI_KEY environment variable not set")
        self.client = OpenAI(api_key=key)  # could also auto infer from environment
        pass

    def generate_response(self, prompt: str) -> str:
        """
        Generate a response using the OpenAI API.
        :param prompt: The prompt to send to the OpenAI model.
        :return: The generated response text.
        """
        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
        )
        return response.output_text

    def generate_pillar_response(self, pillar: Pillar) -> PillarResponse:
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
