import json

import requests
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from helpdesk.models import BackendSessionLog
from helpdesk.session_logging import pop_backend_session_logs

MAX_SESSION_LOG_CHARS = 20000


def get_highest_level(entries):
    priority = {"error": 3, "warning": 2, "warn": 2, "info": 1}

    if not entries:
        return ""

    return max(
        (entry.get("level", "") for entry in entries),
        key=lambda level: priority.get(level, 0),
    )

class HelpdeskTicketView(APIView):
    authentication_classes = []
    permission_classes = []

    # sets up django endpoint for helpdesk (ticket creation)
    def post(self, request):
        ticket_type = str(request.data.get("type", "")).strip()
        title = str(request.data.get("title", "")).strip()
        description = str(request.data.get("description", "")).strip()
        user_contact = str(request.data.get("contact", "")).strip()
        session_logs = request.data.get("logs")
        session_id = str(request.data.get("sessionId", "")).strip()

        if not session_id and isinstance(session_logs, dict):
            session_id = str(session_logs.get("sessionId", "")).strip()

        if not session_id:
            session_id = getattr(request, "pixe_session_id", "")

        # checks request validity & helpdesk config
        if not ticket_type or not title or not description:
            return Response(
                {
                    "error": (
                        "type, title, and description are required "
                        "for creating a ticket"
                    )
                },
                status=400,
            )

        if len(title) > 120:
            return Response({"error": "request title is too long"}, status=400)

        if len(description) > 5000:
            return Response({"error": "description is too long"}, status=400)

        if not settings.GITHUB_HELPDESK_TOKEN:
            return Response({"error": "Helpdesk is not configured"}, status=500)

        # prepares user data for new github issue
        issue_title = f"[{ticket_type}] {title}"
        issue_body = f"""## Request Type
{ticket_type}


## Description
{description}


## Contact Details
{user_contact or "Not provided"}

"""
        is_bug_report = ticket_type == "Bug Report"
        if ticket_type == "Bug Report" and session_id:
            issue_body += f"""
## Debug Session

Session ID: `{session_id}`

Backend logs can be found in Django admin by searching this session ID.

"""

        if session_logs:
            session_logs_json = json.dumps(session_logs, indent=2)

            if len(session_logs_json) > MAX_SESSION_LOG_CHARS:
                session_logs_json = (
                    session_logs_json[:MAX_SESSION_LOG_CHARS]
                    + "\n... session logs truncated ..."
                )

            issue_body += f"""
## Session Logs

```json
{session_logs_json}
```
"""

        # post & create issue
        github_issue_url = (
            "https://api.github.com/repos/"
            f"{settings.GITHUB_HELPDESK_OWNER}/"
            f"{settings.GITHUB_HELPDESK_REPO}/issues"
        )
        github_response = requests.post(
            github_issue_url,
            headers={
                "Authorization": f"Bearer {settings.GITHUB_HELPDESK_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
            json={
                "title": issue_title,
                "body": issue_body,
                "labels": [ticket_type],
            },
            timeout=10,
        )

        if github_response.status_code != 201:
            return Response(
                {"error": "Could not create helpdesk ticket"},
                status=502,
            )

        # creates/appends backend logs in database
        if is_bug_report and session_id:
            # fetches existing session entries if session was logged before
            new_entries = pop_backend_session_logs(session_id)

            with transaction.atomic():
                session_log, created = (
                    BackendSessionLog.objects.select_for_update().get_or_create(
                        session_id=session_id
                    )
                )

                existing_entries = session_log.entries or []
                combined_entries = existing_entries + new_entries

                session_log.entries = combined_entries
                session_log.event_count = len(combined_entries)
                session_log.highest_level = get_highest_level(combined_entries)

                if combined_entries:
                    session_log.first_entry_at = combined_entries[0].get("time")
                    session_log.last_entry_at = combined_entries[-1].get("time")
                else:
                    session_log.first_entry_at = None
                    session_log.last_entry_at = None

                session_log.save()

        issue = github_response.json()

        return Response(
            {
                "number": issue["number"],
                "url": issue["html_url"],
            },
            status=201,
        )
