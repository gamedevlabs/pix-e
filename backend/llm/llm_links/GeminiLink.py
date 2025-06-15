import os

from google import genai

from ..models import Pillar
from .PillarPrompts import ValidationPrompt
from .responseSchemes import FixablePillar, PillarResponse


class GeminiLink:
    """
    Class to interact with the Gemini API.
    """

    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY")
        if key is None:
            raise ValueError("GEMINI_KEY environment variable not set")
        self.client = genai.Client(api_key=key)

    def generate_response(self, prompt: str):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text

    def generate_pillar_response(self, pillar: Pillar) -> PillarResponse:
        """
        Generate a response for a game design pillar.
        :param pillar: The pillar text to analyze.
        :return: A PillarResponse object containing the analysis.
        """
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

    def fix_pillar_through_llm(self, pillar: Pillar) -> Pillar:
        """
        Fix a game design pillar using the Gemini API.
        :param pillar: The pillar to fix.
        """
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
