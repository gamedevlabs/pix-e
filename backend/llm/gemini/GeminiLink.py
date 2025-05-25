import os

from google import genai


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
