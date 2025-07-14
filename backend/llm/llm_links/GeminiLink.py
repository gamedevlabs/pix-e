import os

from google import genai

from . import PillarPrompts
from .LLMLink import LLMLink
from ..models import Pillar
from .PillarPrompts import ValidationPrompt
from .responseSchemes import FixablePillar, PillarResponse, StringFeedback


class GeminiLink(LLMLink):
    """
    Class to interact with the Gemini API.
    """

    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY")
        if key is None:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        self.client = genai.Client(api_key=key)

    def evaluate_pillars_in_context(self, pillars: list[Pillar], context: str) -> StringFeedback:
        prompt = PillarPrompts.OverallFeedbackPrompt % (
                context,
                "\n".join(
                    [f"{pillar.name}:\n {pillar.description}" for pillar in pillars]
                ),
            )
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": StringFeedback,
            },
        )
        return response.parsed

    def evaluate_pillar(self, pillar: Pillar) -> PillarResponse:
        prompt = ValidationPrompt % (pillar.name, pillar.description)
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarResponse,
            },
        )
        return response.parsed

    def improve_pillar(self, pillar: Pillar) -> Pillar:
        prompt = f"""Improve the following Game Design Pillar.
            Check for structural issues regarding the following points:
            1. The title does not match the description.
            2. The intent of the pillar is not clear.
            3. The pillar focuses on more than one aspect.
            4. The description uses bullet points or lists.
            Pillar Title: {pillar.name}\n
            Pillar Description: {pillar.description}
            Rewrite erroneous parts of the pillar and return a new pillar object."""
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": FixablePillar,
            },
        )
        fixed_pillar: FixablePillar = response.parsed
        pillar.name = fixed_pillar.name
        pillar.description = fixed_pillar.description
        pillar.save()
        return pillar

    def evaluate_context_with_pillars(self, pillars: list[Pillar], context: str) -> StringFeedback:
        pass