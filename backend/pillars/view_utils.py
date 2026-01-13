"""
Shared helpers for pillars views.
"""

from typing import Optional

from django.contrib.auth.models import User
from django.db.models import QuerySet

from game_concept.models import GameConcept
from game_concept.utils import get_current_game_concept, get_current_project
from pillars.models import Pillar
from pillars.utils import format_pillars_text


def get_project_pillars(user: User) -> QuerySet[Pillar]:
    project = get_current_project(user)
    queryset = Pillar.objects.filter(user=user)
    if project:
        return queryset.filter(project=project)
    return queryset.filter(project__isnull=True)


def get_project_concept(user: User) -> Optional[GameConcept]:
    project = get_current_project(user)
    return get_current_game_concept(project)


def build_context_payload(
    pillars: list[Pillar], game_concept: GameConcept
) -> tuple[str, str]:
    return format_pillars_text(pillars), game_concept.content


def build_context_payload_from_text(
    pillars: list[Pillar], context_text: str
) -> tuple[str, str]:
    return format_pillars_text(pillars), context_text
