"""Django app configuration for SPARC."""

from django.apps import AppConfig


class SparcConfig(AppConfig):
    """Configuration for SPARC app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "sparc"
    verbose_name = "SPARC Game Design Evaluation"

    def ready(self):
        """Import LLM module to trigger workflow and handler registration."""
        # Import to trigger auto-registration of workflows and handlers
        from sparc.llm import handlers, workflows  # noqa: F401
