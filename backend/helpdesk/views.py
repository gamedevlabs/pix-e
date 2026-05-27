import json

import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

# from llm.logfire_config import get_logfire


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

        # logfire = get_logfire()
        # logfire.info(
            # "helpdesk.ticket_submitted",
            # ticket_type=ticket_type,
            # has_session_logs=bool(session_logs),
        # )

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
        if session_logs:
            issue_body += f"""
## Session Logs

```json
{json.dumps(session_logs, indent=2)}
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

        issue = github_response.json()

        return Response(
            {
                "number": issue["number"],
                "url": issue["html_url"],
            },
            status=201,
        )
