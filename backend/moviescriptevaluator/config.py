import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    # Look for .env in project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed


@dataclass
class Config:
    is_logging_enabled: bool = False
    logging_directory: str = "./moviescriptevaluator/logs/{}-{}-{}.txt"

    @classmethod
    def from_env(cls) -> "Config":
        def get_setting(name: str, default=None, cast_type=str):
            """Get setting from Django or environment."""
            # Try Django settings first
            try:
                from django.conf import settings

                # Check if Django is properly configured
                if settings.configured and hasattr(settings, "MOVIE_SCRIPT_EVAL"):
                    django_config = getattr(settings, "MOVIE_SCRIPT_EVAL")
                    django_value = django_config.get(name.upper())
                    if django_value is not None:
                        return django_value
            except (ImportError, Exception):
                pass  # Django not available or not configured

            env_name = f"MOVIE_SCRIPT_EVAL_{name.upper()}"
            env_value = os.getenv(env_name)

            # If not found, try non-prefixed for common keys
            if env_value is None:
                env_value = os.getenv(name.upper())

            if env_value is None:
                return default

            # Cast to appropriate type
            if cast_type == bool:
                return env_value.lower() in ("true", "1", "yes", "on")
            elif cast_type == int:
                return int(env_value)
            elif cast_type == Path:
                return Path(env_value)
            elif cast_type == list:
                return [s.strip() for s in env_value.split(",")]
            else:
                return env_value

        return cls(
            is_logging_enabled=get_setting("is_logging_enabled", False, bool),
            logging_directory=get_setting(
                "logging_directory", "./moviescriptevaluator/logs/{}-{}-{}.txt", str
            ),
        )


# This is loaded once and can be overridden
_default_config: Optional[Config] = None


# get config of Movie Script Evaluator
def get_config_mse() -> Config:
    global _default_config
    if _default_config is None:
        _default_config = Config().from_env()
    return _default_config
