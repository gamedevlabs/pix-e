from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from helpdesk.models import BackendSessionLog


class Command(BaseCommand):
    help = "Delete old backend session logs from submitted bug reports."

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(days=30)

        deleted_count, _ = BackendSessionLog.objects.filter(
            created_at__lt=cutoff,
        ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted_count} backend session log(s) older than 30 days."
            )
        )