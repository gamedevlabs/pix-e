from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("pillars", "0011_pillar_project_fk"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pillarllmcall",
            name="context_strategy",
        ),
    ]
