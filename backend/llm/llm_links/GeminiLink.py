import os

from google import genai
from google.genai.types import GenerateContentConfigDict

from .LLMLink import LLMLink
from ..models import Pillar
from .prompts import *
from .responseSchemes import *


class GeminiLink(LLMLink):
    """
    Class to interact with the Gemini API.
    """
    MODELNAME = "gemini-2.0-flash"  # Exchange as needed

    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY")
        if key is None:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=key)

    def evaluate_pillar(self, pillar: Pillar) -> PillarResponse:
        prompt = ValidationPrompt % (pillar.name, pillar.description)
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GeminiLink.MODELNAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarResponse,
            },
        )
        return response.parsed

    def improve_pillar(self, pillar: Pillar) -> Pillar:
        prompt = ImprovePillarPrompt % (pillar.name, pillar.description)
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GeminiLink.MODELNAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": LLMPillar,
            },
        )
        fixed_pillar: LLMPillar = response.parsed
        pillar.name = fixed_pillar.name
        pillar.description = fixed_pillar.description
        pillar.save()
        return pillar


    def evaluate_context_with_pillars(self, pillars: list[Pillar],
                                      context: str) -> StringFeedback:
        raise NotImplementedError()

    def evaluate_pillar_completeness(self,
                                     pillars: list[Pillar],
                                     designIdea: str) -> PillarCompletenessResponse:
        prompt = PillarCompletenessPrompt % (
            designIdea,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GeminiLink.MODELNAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarCompletenessResponse,
            },
        )
        return response.parsed

    def evaluate_pillar_contradictions(self,
                                       pillars: list[Pillar],
                                       context: str) -> PillarContradictionResponse:
        prompt = PillarContradictionPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GeminiLink.MODELNAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarContradictionResponse,
            },
        )
        return response.parsed

    def suggest_pillar_additions(self,
                                 pillars: list[Pillar],
                                 context: str) -> PillarAdditionsFeedback:
        prompt = PillarAdditionPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        # noinspection PyTypeChecker
        response = self.client.models.generate_content(
            model=GeminiLink.MODELNAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarAdditionsFeedback,
            },
        )
        return response.parsed
