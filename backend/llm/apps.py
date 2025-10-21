from django.apps import AppConfig


class LlmConfig(AppConfig):
    """
    LLM Orchestrator package configuration.

    This is not a Django app with models - it's a pure Python package
    for LLM orchestration. Included in INSTALLED_APPS to ensure
    proper app loading order and imports.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "llm"
    # Prevent Django from looking for models
    # We're only in INSTALLED_APPS for proper import resolution
