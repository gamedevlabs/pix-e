from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pxnodes", "0009_structuralmemorystate_summary_text_and_more"),
        ("pxcharts", "0009_pxchart_project"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContextArtifact",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("node", "Node"),
                            ("chart", "Chart"),
                            ("path", "Path"),
                            ("concept", "Game Concept"),
                            ("pillar", "Pillar"),
                        ],
                        max_length=20,
                    ),
                ),
                ("scope_id", models.CharField(db_index=True, max_length=128)),
                (
                    "artifact_type",
                    models.CharField(
                        choices=[
                            ("raw_text", "Raw Text"),
                            ("chunks", "Chunks"),
                            ("summary", "Summary"),
                            ("facts", "Atomic Facts"),
                            ("triples", "Knowledge Triples"),
                            ("chart_overview", "Chart Overview"),
                            ("node_list", "Node List"),
                            ("path_summary", "Path Summary"),
                            ("path_snippet", "Path Snippet"),
                            ("milestone", "Milestone"),
                        ],
                        max_length=32,
                    ),
                ),
                ("project_id", models.CharField(blank=True, default="", max_length=128)),
                ("content", models.JSONField()),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("source_hash", models.CharField(db_index=True, max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "chart",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="context_artifacts",
                        to="pxcharts.pxchart",
                    ),
                ),
                (
                    "node",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.CASCADE,
                        related_name="context_artifacts",
                        to="pxnodes.pxnode",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["scope_type", "artifact_type", "scope_id"],
                        name="pxnodes_con_scope_t_a7a08e_idx",
                    ),
                    models.Index(
                        fields=["chart", "scope_type"],
                        name="pxnodes_con_chart_i_69c6a6_idx",
                    ),
                    models.Index(
                        fields=["node", "artifact_type"],
                        name="pxnodes_con_node_id_8b22ea_idx",
                    ),
                ],
                "unique_together": {("scope_type", "scope_id", "artifact_type", "chart", "project_id")},
            },
        ),
        migrations.CreateModel(
            name="ArtifactEmbedding",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("embedding_model", models.CharField(max_length=100)),
                ("embedding_dim", models.IntegerField()),
                ("embedding_hash", models.CharField(db_index=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "artifact",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="embeddings",
                        to="pxnodes.contextartifact",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["artifact", "embedding_model"],
                        name="pxnodes_art_artifac_7f6c8f_idx",
                    ),
                    models.Index(
                        fields=["embedding_hash"],
                        name="pxnodes_art_embedding_9d5395_idx",
                    ),
                ],
            },
        ),
    ]
