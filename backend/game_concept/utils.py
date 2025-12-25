from typing import Optional

from django.contrib.auth.models import User

from .models import GameConcept, Project


def get_current_project(user: User) -> Optional[Project]:
    """Return the user's current project if set."""
    return Project.objects.filter(user=user, is_current=True).first()


def get_current_game_concept(project: Optional[Project]) -> Optional[GameConcept]:
    """Return the current game concept for the given project, if set."""
    if not project:
        return None
    return GameConcept.objects.filter(project=project, is_current=True).first()
