from django.db import migrations, models
import django.db.models.deletion


def create_projects_from_concepts(apps, schema_editor):
    GameConcept = apps.get_model("game_concept", "GameConcept")
    Project = apps.get_model("game_concept", "Project")
    db_alias = schema_editor.connection.alias

    for concept in GameConcept.objects.using(db_alias).all():
        content = (concept.content or "").strip()
        name = content.split("\n")[0] if content else ""
        if len(name) > 255:
            name = name[:255]
        if not name:
            name = f"Project {concept.id}"

        Project.objects.using(db_alias).create(
            id=concept.id,
            user=concept.user,
            name=name,
            description="",
            is_current=concept.is_current,
        )
        concept.project_id = concept.id
        concept.save(update_fields=["project"])


class Migration(migrations.Migration):
    dependencies = [
        ("game_concept", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, default="", max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "is_current",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this is the user's current project",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AddField(
            model_name="gameconcept",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="game_concepts",
                to="game_concept.project",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="gameconcept",
            name="one_current_per_user",
        ),
        migrations.AddConstraint(
            model_name="gameconcept",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_current", True)),
                fields=("project",),
                name="one_current_concept_per_project",
            ),
        ),
        migrations.AddConstraint(
            model_name="project",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_current", True)),
                fields=("user",),
                name="one_current_project_per_user",
            ),
        ),
        migrations.RunPython(create_projects_from_concepts, migrations.RunPython.noop),
    ]
