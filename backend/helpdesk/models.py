from django.db import models


class BackendSessionLog(models.Model):
    # One database row per submitted bug-report session.
    session_id = models.CharField(max_length=64, unique=True, db_index=True)

    # Aggregated backend log entries for this session.
    entries = models.JSONField(default=list, blank=True)

    event_count = models.PositiveIntegerField(default=0)
    highest_level = models.CharField(max_length=20, blank=True, default="")

    # Optional summary fields for faster admin scanning.
    first_entry_at = models.DateTimeField(null=True, blank=True)
    last_entry_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.session_id} - {self.event_count} backend events"
