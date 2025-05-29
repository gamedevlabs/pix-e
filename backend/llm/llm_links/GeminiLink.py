import os

from google import genai
from . responseSchemes import PillarResponse
from ..models import Pillar



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
        prompt = (
            f"""Validate the following Game Design Pillar. Check for structural issues 
            regarding the following points:
            1. The title does not match the description.
            2. The intent of the pillar is not clear.
            3. The pillar focuses on more than one aspect.
            Pillar Title: {pillar.title}\n
            Pillar Description: {pillar.description}
            Then give feedback on the pillar and if it could be improved.
            Answer directly as if you are giving your feedback to the designer."""
        )
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": PillarResponse,
            },
        )
        return response.parsed
