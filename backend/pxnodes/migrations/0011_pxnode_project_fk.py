from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("game_concept", "0002_project_model_and_links"),
        ("pxnodes", "0010_context_artifact_inventory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pxnode",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pxnodes",
                to="game_concept.project",
            ),
        ),
        migrations.AlterField(
            model_name="pxcomponentdefinition",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pxcomponentdefinitions",
                to="game_concept.project",
            ),
        ),
    ]
