import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("sparc", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameConcept",
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
                ("content", models.TextField(help_text="The game idea text")),
                (
                    "is_current",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this is the user's current game concept",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "last_sparc_evaluation",
                    models.ForeignKey(
                        blank=True,
                        help_text="Link to the most recent SPARC evaluation for this concept",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="sparc.sparcevaluation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("is_current", True)),
                        fields=("user",),
                        name="one_current_per_user",
                    )
                ],
            },
        ),
    ]
