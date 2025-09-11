from django.apps import AppConfig


class PxChartsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pxcharts"

    # This import actually is used (in some way that I do not 100% understand)
    # With this import whenever a PxChartContainer is created,
    # it also adds an instance in the layout table for that PxChartContainer
    def ready(self):
        import pxcharts.signals  # noqa: F401
