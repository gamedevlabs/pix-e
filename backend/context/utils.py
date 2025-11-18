"""
Context utility functions for retrieving and managing user context.

These utilities provide centralized context retrieval, prompt formatting,
and coherence checking across all features.
"""

from typing import Any, List

from django.contrib.auth.models import User

from .schemas import CoherenceReport, UserContext


def get_user_context(
    user: User, include: List[str] = ["pillars", "sparc", "game_concept"]
) -> UserContext:
    """
    Retrieve all context data for a user.
    """
    raise NotImplementedError("Context retrieval coming soon")


def format_context_for_prompt(context_data: UserContext) -> str:
    """
    Format context data into a structured prompt section.

    """
    raise NotImplementedError("Context formatting coming soon")


def check_coherence(
    new_content: Any, context_data: UserContext, feature_type: str
) -> CoherenceReport:
    """
    Check if new content maintains coherence with existing context.

    """
    raise NotImplementedError("Coherence checking coming soon")
