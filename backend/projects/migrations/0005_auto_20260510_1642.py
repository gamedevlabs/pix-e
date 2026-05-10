from django.db import migrations
from django.conf import settings


def create_projects_and_attach_elements(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Pillar = apps.get_model("pillars", "Pillar")
    GameConcept = apps.get_model("game_concept", "GameConcept")
    PxChart = apps.get_model("pxcharts", "PxChart")
    PxNode = apps.get_model("pxnodes", "PxNode")
    PxComponentDefinition = apps.get_model("pxnodes", "PxComponentDefinition")

    user_ids = set()

    user_ids.update(
        Pillar.objects.filter(project__isnull=True)
        .values_list("user_id", flat=True)
        .distinct()
    )
    user_ids.update(
        GameConcept.objects.filter(project__isnull=True)
        .values_list("user_id", flat=True)
        .distinct()
    )
    user_ids.update(
        PxChart.objects.filter(project__isnull=True)
        .values_list("owner_id", flat=True)
        .distinct()
    )
    user_ids.update(
        PxNode.objects.filter(project__isnull=True)
        .values_list("owner_id", flat=True)
        .distinct()
    )
    user_ids.update(
        PxComponentDefinition.objects.filter(project__isnull=True)
        .values_list("owner_id", flat=True)
        .distinct()
    )

    for user_id in user_ids:
        project = Project.objects.create(
            user_id=user_id,
            name="Migrated Project",
        )

        Pillar.objects.filter(
            user_id=user_id,
            project__isnull=True,
        ).update(project=project)

        GameConcept.objects.filter(
            user_id=user_id,
            project__isnull=True,
        ).update(project=project)

        PxChart.objects.filter(
            owner_id=user_id,
            project__isnull=True,
        ).update(project=project)

        PxNode.objects.filter(
            owner_id=user_id,
            project__isnull=True,
        ).update(project=project)

        PxComponentDefinition.objects.filter(
            owner_id=user_id,
            project__isnull=True,
        ).update(project=project)


def reverse_migration(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Pillar = apps.get_model("pillars", "Pillar")
    GameConcept = apps.get_model("game_concept", "GameConcept")
    PxChart = apps.get_model("pxcharts", "PxChart")
    PxNode = apps.get_model("pxnodes", "PxNode")
    PxComponentDefinition = apps.get_model("pxnodes", "PxComponentDefinition")

    migrated_projects = Project.objects.filter(name="Migrated Project")

    Pillar.objects.filter(project__in=migrated_projects).update(project=None)
    GameConcept.objects.filter(project__in=migrated_projects).update(project=None)
    PxChart.objects.filter(project__in=migrated_projects).update(project=None)
    PxNode.objects.filter(project__in=migrated_projects).update(project=None)
    PxComponentDefinition.objects.filter(project__in=migrated_projects).update(
        project=None
    )

    migrated_projects.delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("projects", "0004_remove_project_target_platform_and_more"),
        ("pillars", "0014_alter_pillar_project"),
        ("game_concept", "0005_delete_project"),
        ("pxcharts", "0012_alter_pxchart_project_alter_pxchartcontainer_owner"),
        ("pxnodes", "0014_alter_pxcomponentdefinition_owner_and_more"),
    ]

    operations = [
        migrations.RunPython(
            create_projects_and_attach_elements,
            reverse_migration,
        ),
    ]
