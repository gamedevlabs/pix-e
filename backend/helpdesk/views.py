import requests
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView


class HelpdeskTicketView(APIView):
    authentication_classes = []
    permission_classes = []

    # sets up django endpoint for helpdesk (ticket creation)
    def post(self, request):
        ticket_type = str(request.data.get("type", "")).strip()
        title = str(request.data.get("title", "")).strip()
        description = str(request.data.get("description", "")).strip()
        user_contact = str(request.data.get("contact", "")).strip()

        # checks request validity & helpdesk config
        if not ticket_type or not title or not description:
            return Response(
                {
                    "error": "type, title, and description are required for creating a ticket"
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

        # post & create issue
        github_response = requests.post(
            f"https://api.github.com/repos/{settings.GITHUB_HELPDESK_OWNER}/{settings.GITHUB_HELPDESK_REPO}/issues",
            headers={
                "Authorization": f"Bearer {settings.GITHUB_HELPDESK_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
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
