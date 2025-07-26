from abc import ABC, abstractmethod

from llm.llm_links.responseSchemes import StringFeedback, PillarResponse, \
    PillarsInContextResponse,
from llm.models import Pillar


class LLMLink(ABC):
    @abstractmethod
    def evaluate_pillar(self, pillar: Pillar) -> PillarResponse:
        """
        Generate a response for a game design pillar.
        :param pillar: The pillar text to analyze.
        :return: A PillarResponse object containing the analysis.
        """
        pass

    @abstractmethod
    def evaluate_pillars_in_context(self,
                                    pillars: list[Pillar],
                                    context: str) -> PillarsInContextResponse:
        """
        Generate a response for a list of game design pillars in a given context.
        :param pillars: A list of Pillar objects to analyze.
        :param context: The context in which to evaluate the pillars.
        :return: A StringFeedback object containing the evaluation results.
        """
        pass

    @abstractmethod
    def improve_pillar(self, pillar: Pillar) -> Pillar:
        """
        Improve a game design pillar using the LLM.
        This method will store the improved pillar in the database.
        :param pillar: The pillar to improve.
        :return: The improved Pillar object.
        """
        pass

    @abstractmethod
    def evaluate_context_with_pillars(self,
                                      pillars: list[Pillar],
                                      context: str) -> StringFeedback:
        """
        Evaluate the context against a list of pillars.
        :param pillars: A list of Pillar objects to use for evaluation.
        :param context: The context to evaluate.
        :return: A StringFeedback object containing the evaluation results.
        """
        pass

    @abstractmethod
    def evaluate_pillar_contradictions(self,
                                       pillars: list[Pillar],
                                       context: str) -> PillarContradictionResponse:
        pass

    @abstractmethod
    def evaluate_pillar_completeness(self,
                                      pillars: list[Pillar],
                                      context: str) -> PillarCompletenessResponse:
        """
        Evaluate if the context is sufficiently covered by the pillars.
        :param pillars: A list of Pillar objects to use for evaluation.
        :param context: The context to evaluate.
        :return: A StringFeedback object containing the evaluation results.
        """
        pass