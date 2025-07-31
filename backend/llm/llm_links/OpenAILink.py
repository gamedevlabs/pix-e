import os

from openai import OpenAI

from llm.llm_links.LLMLink import LLMLink
from llm.llm_links.prompts import *
from llm.llm_links.responseSchemes import PillarResponse, StringFeedback, LLMPillar, \
    PillarsInContextResponse, PillarCompletenessResponse, PillarContradictionResponse, \
    PillarAdditionsFeedback, ContextInPillarsResponse
from llm.models import Pillar


class OpenAILink(LLMLink):
    MODELNAME = "gpt-4o-mini"  # Exchange as needed
    def __init__(self):
        key = os.environ.get("OPENAI_API_KEY")
        if key is None:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.client = OpenAI(api_key=key)  # could also auto infer from environment
        pass

    def evaluate_pillar(self, pillar: Pillar) -> PillarResponse:
        prompt = ValidationPrompt % (pillar.name, pillar.description)
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=PillarResponse,
        )
        response: PillarResponse = response.output_parsed
        # todo(reenable after testing) Filtering issues with low severity (only necessary for GPT)
        # response.structuralIssues = [
        #    issue for issue in response.structuralIssues if issue.severity >= 2
        # ]
        # response.hasStructureIssue = len(response.structuralIssues) > 0
        return response

    def improve_pillar(self, pillar: Pillar) -> Pillar:
        prompt = ImprovePillarPrompt % (pillar.name, pillar.description)
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=LLMPillar,
        )
        fixed_pillar: LLMPillar = response.output_parsed
        pillar.name = fixed_pillar.name
        pillar.description = fixed_pillar.description
        pillar.save()
        return pillar

    def evaluate_pillar_completeness(self,
                                     pillars: list[Pillar],
                                     context: str) -> PillarCompletenessResponse:
        prompt = PillarCompletenessPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=PillarCompletenessResponse,
        )
        return response.output_parsed

    def evaluate_pillar_contradictions(self,
                                       pillars: list[Pillar],
                                       context: str) -> PillarContradictionResponse:
        prompt = PillarContradictionPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=PillarContradictionResponse,
        )
        return response.output_parsed

    def suggest_pillar_additions(self,
                                 pillars: list[Pillar],
                                 context: str) -> PillarAdditionsFeedback:
        prompt = PillarAdditionPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=PillarAdditionsFeedback,
        )
        return response.output_parsed

    def evaluate_context_with_pillars(self, pillars: list[Pillar],
                                      context: str) -> ContextInPillarsResponse:
        prompt = ContextInPillarsPrompt % (
            context,
            "\n".join([pillar.__str__() for pillar in pillars]),
        )
        response = self.client.responses.parse(
            model=OpenAILink.MODELNAME,
            input=prompt,
            text_format=ContextInPillarsResponse,
        )
        return response.output_parsed
