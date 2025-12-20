from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pillars", "0008_persist_pillar_llm_calls"),
    ]

    operations = [
        migrations.AddField(
            model_name="pillarllmcall",
            name="context_strategy",
            field=models.CharField(default="raw", max_length=50),
        ),
    ]
