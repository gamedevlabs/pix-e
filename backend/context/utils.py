"""
Context utility functions for retrieving and managing user context.

These utilities provide centralized context retrieval, prompt formatting,
and coherence checking across all features.
"""

from typing import Any, Dict, List

from django.contrib.auth.models import User

from .schemas import CoherenceReport, PillarData, UserContext


def get_user_context(
    user: User, include: List[str] = ["pillars", "sparc", "game_concept"]
) -> UserContext:
    """
    Retrieve all context data for a user.

    Args:
        user: The user to get context for
        include: List of context sources to include
                 Options: "pillars", "sparc", "game_concept"

    Returns:
        UserContext object with requested data
    """
    from game_concept.utils import get_current_game_concept, get_current_project
    from pillars.models import Pillar

    context_data: Dict[str, Any] = {
        "game_concept": None,
        "pillars": [],
        "sparc_evaluation": None,
        "last_updated": {},
    }

    # Retrieve game concept if requested
    if "game_concept" in include:
        project = get_current_project(user)
        game_concept = get_current_game_concept(project)
        if game_concept:
            context_data["game_concept"] = game_concept.content
            context_data["last_updated"]["game_concept"] = game_concept.updated_at

    # Retrieve pillars if requested
    if "pillars" in include:
        project = get_current_project(user)
        pillar_queryset = Pillar.objects.filter(user=user)
        if project:
            pillar_queryset = pillar_queryset.filter(project=project)
        else:
            pillar_queryset = pillar_queryset.filter(project__isnull=True)
        pillars = pillar_queryset.only(
            "id", "name", "description", "created_at"
        ).order_by("-created_at")

        context_data["pillars"] = [
            PillarData(
                id=p.id,
                name=p.name,
                description=p.description,
                created_at=p.created_at,
            )
            for p in pillars
        ]

        if pillars:
            latest_pillar = pillars[0] if pillars else None
            if latest_pillar:
                context_data["last_updated"]["pillars"] = latest_pillar.created_at

    # Retrieve SPARC evaluation if requested
    if "sparc" in include:
        pass  # SPARC context retrieval coming soon

    return UserContext(**context_data)


def format_context_for_prompt(context_data: UserContext) -> str:
    """
    Format context data into a structured prompt section.

    Args:
        context_data: UserContext object to format

    Returns:
        Formatted string ready to be injected into LLM prompts
    """
    sections = []

    # Add game concept section
    if context_data.game_concept:
        sections.append("GAME CONCEPT:")
        sections.append(context_data.game_concept)
        sections.append("")

    # Add pillars section
    if context_data.pillars:
        sections.append("DESIGN PILLARS:")
        for i, pillar in enumerate(context_data.pillars, 1):
            sections.append(f"{i}. {pillar.name}: {pillar.description}")
        sections.append("")

    # Add SPARC evaluation section
    if context_data.sparc_evaluation:
        sparc = context_data.sparc_evaluation
        sections.append("SPARC EVALUATION:")
        sections.append(f"Overall Score: {sparc.overall_score}/100")
        sections.append(f"Readiness: {sparc.readiness_status}")
        sections.append("")

    if not sections:
        return "No context available."

    return "\n".join(sections).strip()


def check_coherence(
    new_content: Any, context_data: UserContext, feature_type: str
) -> CoherenceReport:
    """
    Check if new content maintains coherence with existing context.

    Args:
        new_content: The new pillar/node/etc being created
        context_data: Existing user context
        feature_type: "pillar" | "sparc" | "node"

    Returns:
        CoherenceReport with issues, suggestions, and severity
    """
    # Stub implementation for now
    return CoherenceReport(
        is_coherent=True,
        severity="none",
        issues=[],
        suggestions=[],
        affected_features=[],
    )
