"""Django app configuration for SPARC."""

from django.apps import AppConfig


class SparcConfig(AppConfig):
    """Configuration for SPARC app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sparc"
    verbose_name = "SPARC Game Design Evaluation"

    def ready(self):
        """Initialize SPARC app."""
        pass
