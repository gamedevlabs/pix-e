import re
from pathlib import Path
from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from game_concept.models import GameConcept, Project


def _iter_concept_files(source_dir: Path, include_summaries: bool) -> Iterable[Path]:
    if not source_dir.exists():
        raise CommandError(f"Source directory not found: {source_dir}")
    for path in sorted(source_dir.glob("*.txt")):
        if not include_summaries and "summary" in path.name.lower():
            continue
        yield path


def _clean_project_name(stem: str) -> str:
    name = re.sub(r"_(Game|Summary).*", "", stem, flags=re.IGNORECASE)
    return name.replace("_", " ").strip() or stem


def _build_description(path: Path) -> str:
    notes = [
        f"source_file={path.name}",
        "note=prefix at_least_N_M means prompt asked for at least N aspects and "
        "the model included M aspects",
        "note=duplicate titles may exist (e.g., Echoes of Orbis) with distinct content",
    ]
    stem_lower = path.stem.lower()
    if "at_least" in stem_lower or "exactly" in stem_lower:
        notes.append(f"prompt_hint={path.stem}")
    return "\n".join(notes)


class Command(BaseCommand):
    help = "Import SPARC game concepts from docs/GameIdeas into the database."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--user-id", type=int, default=2)
        parser.add_argument(
            "--source-dir",
            default="docs/GameIdeas",
            help="Directory containing SPARC concept .txt files.",
        )
        parser.add_argument(
            "--include-summaries",
            action="store_true",
            help="Also import summary files (default: skip).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of files imported.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be imported without writing to the DB.",
        )

    def handle(self, *args, **options) -> None:
        user_id = options["user_id"]
        source_dir = Path(options["source_dir"]).resolve()
        include_summaries = options["include_summaries"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        user_model = get_user_model()
        try:
            user = user_model.objects.get(id=user_id)
        except user_model.DoesNotExist as exc:
            raise CommandError(f"User not found: {user_id}") from exc

        files = list(_iter_concept_files(source_dir, include_summaries))
        if limit is not None:
            files = files[: max(0, limit)]

        if not files:
            self.stdout.write(self.style.WARNING("No concept files found."))
            return

        created_projects = 0
        created_concepts = 0

        for path in files:
            content = path.read_text(encoding="utf-8").strip()
            if not content:
                self.stdout.write(self.style.WARNING(f"Skipping empty file: {path}"))
                continue

            base_name = _clean_project_name(path.stem)
            name = base_name
            suffix = 2
            while Project.objects.filter(user=user, name=name).exists():
                name = f"{base_name} ({suffix})"
                suffix += 1

            description = _build_description(path)

            if dry_run:
                self.stdout.write(f"[dry-run] Project='{name}' Concept='{path.name}'")
                continue

            project = Project.objects.create(
                user=user,
                name=name,
                description=description,
                is_current=False,
            )
            created_projects += 1

            GameConcept.objects.filter(project=project, is_current=True).update(
                is_current=False
            )
            GameConcept.objects.create(
                user=user,
                project=project,
                content=content,
                is_current=True,
            )
            created_concepts += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created_concepts} concepts "
                f"across {created_projects} projects."
            )
        )
