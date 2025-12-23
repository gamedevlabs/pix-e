from typing import Optional

from django.contrib.auth.models import User

from .models import GameConcept


def get_current_project(user: User) -> Optional[GameConcept]:
    """Return the user's current project (game concept) if set."""
    return GameConcept.objects.filter(user=user, is_current=True).first()
