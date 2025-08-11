from django.apps import AppConfig


class MoodboardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "moodboards"
    verbose_name = "Moodboards"

    def ready(self):
        """Import signal handlers when Django starts"""
        try:
            import moodboards.signals
        except ImportError:
            pass
