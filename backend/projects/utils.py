from django.contrib.auth.models import User

from .models import Project


def get_current_project(user: User) -> Project:
    """Return the user's current project if set."""
    return Project.objects.get(user=user, is_current=True)
