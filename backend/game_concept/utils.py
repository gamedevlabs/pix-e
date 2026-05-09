from typing import Optional

from projects.models import Project
from .models import GameConcept


def get_current_game_concept(project: Optional[Project]) -> Optional[GameConcept]:
    """Return the current game concept for the given project, if set."""
    if not project:
        return None
    return GameConcept.objects.filter(project=project, is_current=True).first()
