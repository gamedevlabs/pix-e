from __future__ import annotations

from dataclasses import dataclass
from typing import List

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from pydantic import BaseModel, Field

from game_concept.models import GameConcept, Project
from llm.providers.manager import ModelManager
from pillars.models import Pillar


class PillarItem(BaseModel):
    name: str = Field(description="Short pillar name")
    description: str = Field(description="1-2 sentence pillar description")


class PillarSet(BaseModel):
    pillars: List[PillarItem] = Field(description="List of design pillars")


@dataclass
class PillarRequest:
    concept_text: str
    min_pillars: int
    max_pillars: int

    def prompt(self) -> str:
        return (
            "You are a game design expert. Based on the game concept below, "
            f"generate {self.min_pillars} to {self.max_pillars} distinct design "
            "pillars. Each pillar must be specific, non-overlapping, and useful "
            "for guiding design decisions. Return JSON only.\n\n"
            "Game Concept:\n"
            f"{self.concept_text}\n"
        )


class Command(BaseCommand):
    help = "Generate 4-6 design pillars per SPARC concept using gpt-4o-mini."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--user-id", type=int, default=2)
        parser.add_argument("--model", default="gpt-4o-mini")
        parser.add_argument("--min-pillars", type=int, default=4)
        parser.add_argument("--max-pillars", type=int, default=6)
        parser.add_argument(
            "--project-id",
            type=int,
            default=None,
            help="Limit to a single project id.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of projects processed.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing pillars for the project before inserting new ones.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without writing to the DB.",
        )

    def handle(self, *args, **options) -> None:
        user_id = options["user_id"]
        model_name = options["model"]
        min_pillars = options["min_pillars"]
        max_pillars = options["max_pillars"]
        project_id = options["project_id"]
        limit = options["limit"]
        replace = options["replace"]
        dry_run = options["dry_run"]

        if min_pillars < 1 or max_pillars < min_pillars:
            raise CommandError("Invalid min/max pillar bounds.")

        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist as exc:
            raise CommandError(f"User not found: {user_id}") from exc

        projects = Project.objects.filter(user=user).order_by("id")
        if project_id:
            projects = projects.filter(id=project_id)
        if limit is not None:
            projects = projects[: max(0, limit)]

        if not projects:
            self.stdout.write(self.style.WARNING("No projects found to process."))
            return

        model_manager = ModelManager()
        created_total = 0

        for project in projects:
            concept = (
                GameConcept.objects.filter(project=project, is_current=True)
                .order_by("-updated_at")
                .first()
            )
            if not concept:
                self.stdout.write(
                    self.style.WARNING(f"Skipping project without concept: {project}")
                )
                continue

            if (
                not replace
                and Pillar.objects.filter(user=user, project=project).exists()
            ):
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping project with existing pillars: {project.name}"
                    )
                )
                continue

            if replace and not dry_run:
                Pillar.objects.filter(user=user, project=project).delete()

            request = PillarRequest(
                concept_text=concept.content,
                min_pillars=min_pillars,
                max_pillars=max_pillars,
            )

            if dry_run:
                self.stdout.write(
                    f"[dry-run] Would generate pillars for '{project.name}'"
                )
                continue

            result = model_manager.generate_structured_with_model(
                model_name=model_name,
                prompt=request.prompt(),
                response_schema=PillarSet,
                temperature=0,
            )

            data = result.data if hasattr(result, "data") else result
            pillars = getattr(data, "pillars", None) or data.get("pillars", [])

            # Enforce upper bound without re-calling the model.
            pillars = list(pillars)[:max_pillars]
            if len(pillars) < min_pillars:
                self.stdout.write(
                    self.style.WARNING(
                        f"Only {len(pillars)} pillars generated for '{project.name}'"
                    )
                )

            created = 0
            for item in pillars:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    description = item.get("description", "")
                else:
                    name = getattr(item, "name", "")
                    description = getattr(item, "description", "")
                if not name or not description:
                    continue
                Pillar.objects.create(
                    user=user,
                    project=project,
                    name=name.strip(),
                    description=description.strip(),
                )
                created += 1

            created_total += created
            self.stdout.write(
                self.style.SUCCESS(f"Generated {created} pillars for '{project.name}'")
            )

        self.stdout.write(self.style.SUCCESS(f"Total pillars created: {created_total}"))
