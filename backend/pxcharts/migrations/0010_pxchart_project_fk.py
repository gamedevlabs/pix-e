from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("game_concept", "0002_project_model_and_links"),
        ("pxcharts", "0009_pxchart_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pxchart",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pxcharts",
                to="game_concept.project",
            ),
        ),
    ]
