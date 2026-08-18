"""Seed a structured eval-dataset JSON (pillars + nodes + optional components)
into an EXISTING pix:e project via the ORM.

Unlike ``pxnodes/llm/eval/loader.py`` (which loads a fully *frozen* export incl.
charts/containers/edges into a throwaway eval project), this seeds only the
*content* — pillars, nodes, and optional component values — into a real project
you created in the tool. The chart graph (edges) is then drawn by hand in the UI,
and the whole thing is frozen with ``export_eval_dataset``.

Input JSON schema:
    {
      "pillars": [{"name": "...", "description": "..."}],
      "component_definitions": [{"name": "Recommended Level", "type": "number"}],
      "nodes": [
        {"name": "...", "description": "...",
         "components": {"Recommended Level": 13, "Gym Type": "Rock"}}
      ]
    }
(`type` ∈ {"number", "string", "boolean"}; "components" is optional.)

Usage:
    python manage.py seed_pokemon_dataset \\
        --project-id 7 \\
        --input ~/Documents/thesis/bachelorarbeit/pokemon_kanto_seed.json \\
        [--wipe]

IMPORTANT: run this in the SAME environment as the running app (e.g. inside the
docker container if the UI runs via docker) so it writes to the DB the browser
reads — otherwise the seeded nodes won't show up in your project.
"""

import json
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pillars.models import Pillar
from projects.models import Project
from pxnodes.models import PxComponent, PxComponentDefinition, PxNode


class Command(BaseCommand):
    help = "Seed pillars + nodes (+ components) from JSON into an existing project."

    def add_arguments(self, parser):
        parser.add_argument("--project-id", type=int, required=True)
        parser.add_argument("--input", type=str, required=True)
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete the project's existing pillars/defs/nodes before seeding.",
        )

    def handle(self, *args, **options):
        path = Path(options["input"]).expanduser()
        if not path.exists():
            raise CommandError(f"Input not found: {path}")
        data = json.loads(path.read_text())

        try:
            project = Project.objects.get(id=options["project_id"])
        except Project.DoesNotExist:
            raise CommandError(f"Project {options['project_id']} not found")
        user = project.user

        pillars = data.get("pillars", [])
        defs = data.get("component_definitions", [])
        nodes = data.get("nodes", [])

        with transaction.atomic():
            if options["wipe"]:
                d1 = Pillar.objects.filter(project=project).delete()[0]
                d2 = PxComponentDefinition.objects.filter(project=project).delete()[0]
                d3 = PxNode.objects.filter(project=project).delete()[0]
                self.stdout.write(
                    self.style.WARNING(
                        f"Wiped existing pillars/defs/nodes: {d1}/{d2}/{d3}"
                    )
                )

            for p in pillars:
                Pillar.objects.create(
                    user=user,
                    project=project,
                    name=p["name"],
                    description=p.get("description", ""),
                )

            # PxComponentDefinition / PxNode / PxComponent use UUID primary keys
            # with no default — the id must be supplied explicitly (mirrors
            # loader.py). Pillar uses an auto integer PK, so it needs no id.
            def_by_name = {}
            for d in defs:
                def_by_name[d["name"]] = PxComponentDefinition.objects.create(
                    id=uuid.uuid4(),
                    name=d["name"],
                    type=d["type"],
                    owner=user,
                    project=project,
                )

            n_nodes = n_comp = 0
            for n in nodes:
                node = PxNode.objects.create(
                    id=uuid.uuid4(),
                    name=n["name"],
                    description=n.get("description", ""),
                    owner=user,
                    project=project,
                )
                n_nodes += 1
                for cname, cval in (n.get("components") or {}).items():
                    defn = def_by_name.get(cname)
                    if defn is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  node '{n['name']}': unknown component "
                                f"'{cname}' — skipped"
                            )
                        )
                        continue
                    PxComponent.objects.create(
                        id=uuid.uuid4(),
                        node=node,
                        definition=defn,
                        value=cval,
                        owner=user,
                    )
                    n_comp += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded into project {project.id} ('{project.name}'): "
                f"{len(pillars)} pillars, {len(defs)} component defs, "
                f"{n_nodes} nodes, {n_comp} components."
            )
        )
