from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("game_concept", "0002_project_model_and_links"),
        ("pillars", "0010_pillar_project"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pillar",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pillars",
                to="game_concept.project",
            ),
        ),
    ]
