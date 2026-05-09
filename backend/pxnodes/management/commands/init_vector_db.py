"""Management command to initialize the vector database for structural memory."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Initialize the vector database for structural memory context."""

    help = "Initialize the sqlite-vec vector database for structural memory"

    def handle(self, *args, **options):
        """Execute the command."""
        from pxnodes.llm.context.vector_store import (
            VECTOR_DB_PATH,
            init_database,
        )

        self.stdout.write(f"Database path: {VECTOR_DB_PATH}")
        self.stdout.write("Initializing vector database...")

        vec_available = init_database()

        if vec_available:
            self.stdout.write(
                self.style.SUCCESS(
                    "Vector database initialized with sqlite-vec support!"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Vector database initialized in FALLBACK mode.\n"
                    "Vector similarity search will NOT be available.\n"
                    "On macOS, use Homebrew Python: brew install python"
                )
            )
