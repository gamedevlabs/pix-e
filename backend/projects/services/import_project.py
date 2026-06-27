from rest_framework.exceptions import ValidationError

# from projects.import_serializers import ProjectImportSerializer
# from pxcharts.services.import_project import import_project_data as import_pxcharts
# from pxnodes.services.import_project import import_project_data as import_pxnodes

from projects.serializers import ProjectTransferSerializer
from projects.models import Project

SUPPORTED_VERSION = 1


def import_project_export(payload, user):
    version = payload.get("version")

    if version != SUPPORTED_VERSION:
        raise ValidationError(f"Unsupported export version: {version}")

    project_data = payload.get("project")

    if not project_data:
        raise ValidationError("Missing project data.")

    project_data["name"] = get_available_project_name(user=user, base_name=project_data["name"])

    serializer = ProjectTransferSerializer(data=project_data)
    serializer.is_valid(raise_exception=True)

    project = serializer.save(user=user)  # or user=user, depending on your model

    # import_pxcharts(project, payload)
    # import_pxnodes(project, payload)

    return project


def get_available_project_name(user, base_name):
    existing_names = set(
        Project.objects
        .filter(user=user, name__startswith=base_name)
        .values_list("name", flat=True)
    )

    if base_name not in existing_names:
        return base_name

    n = 1
    while f"{base_name} ({n})" in existing_names:
        n += 1

    return f"{base_name} ({n})"