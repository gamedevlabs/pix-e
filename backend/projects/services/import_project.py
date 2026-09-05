from rest_framework.exceptions import ValidationError

from game_concept.models import GameConcept
from pillars.models import Pillar
from projects.models import Project
from projects.serializers import ProjectTransferSerializer
from pxcharts.services.transfer import import_project_data as import_chart_data
from pxnodes.services.transfer import import_project_data as import_node_data


def import_project_data(payload, user):
    project_data = payload.get("project")

    if not project_data:
        raise ValidationError("Missing project data.")

    project_data["name"] = get_available_project_name(
        user=user, base_name=project_data["name"]
    )

    serializer = ProjectTransferSerializer(data=project_data)
    serializer.is_valid(raise_exception=True)

    project = serializer.save(user=user)

    for d in payload.get("pillars", []):
        Pillar.objects.create(
            user=user,
            project=project,
            name=d["name"],
            description=d["description"],
        )

    concept = payload.get("game_concept")
    if concept:
        GameConcept.objects.create(
            user=user,
            project=project,
            content=concept["content"],
            is_current=True,
        )

    node_map, lock_definitions_map = import_node_data(project, payload, user)
    import_chart_data(project, payload, user, node_map, lock_definitions_map)

    return project


def get_available_project_name(user, base_name):
    existing_names = set(
        Project.objects.filter(user=user, name__startswith=base_name).values_list(
            "name", flat=True
        )
    )

    if base_name not in existing_names:
        return base_name

    n = 1
    while f"{base_name} ({n})" in existing_names:
        n += 1

    return f"{base_name} ({n})"
