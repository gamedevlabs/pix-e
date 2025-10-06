from django.db import migrations
import pandas as pd
from pathlib import Path


def load_seed_data(apps, schema_editor):
    """
    Populate PlayerExpectationsAbsa and PlayerExpectationsConfusions
    tables from CSV files in ../seeds/.
    """

    # Dynamically get model classes (avoid direct imports)
    PlayerExpectationsAbsa = apps.get_model("player_expectations", "PlayerExpectationsAbsa")
    PlayerExpectationsConfusions = apps.get_model("player_expectations", "PlayerExpectationsConfusions")

    # ---------- resolve paths ----------
    base_dir = Path(__file__).resolve().parent.parent  # one level above 'migrations'
    seeds_dir = base_dir / "seeds"
    absa_path = seeds_dir / "ABSA_results.csv"
    confusions_path = seeds_dir / "confusions.csv"

    if not absa_path.exists():
        print(f"[seed_data] WARNING: {absa_path} not found, skipping PlayerExpectationsAbsa seeding.")
    else:
        df_absa = pd.read_csv(absa_path)
        df_absa = df_absa.replace({pd.NA: None})
        records = df_absa.to_dict(orient="records")

        objs = [
            PlayerExpectationsAbsa(
                unnamed_0=row.get("Unnamed: 0"),
                appid=row.get("appid"),
                name=row.get("name"),
                release_date=row.get("release_date"),
                required_age=row.get("required_age"),
                price=row.get("price"),
                dlc_count=row.get("dlc_count"),
                categories=row.get("categories"),
                genres=row.get("genres"),
                user_score=row.get("user_score"),
                positive=row.get("positive"),
                negative=row.get("negative"),
                tags=row.get("tags"),
                review_text=row.get("review_text"),
                explicit_expectations=row.get("explicit_expectations"),
                has_explicit=row.get("has_explicit"),
                expectations=row.get("expectations"),
                absa_expectations=row.get("ABSA_expectations"),
                dominant_aspect=row.get("dominant_aspect"),
                dominant_sentiment=row.get("dominant_sentiment"),
            )
            for row in records
        ]

        PlayerExpectationsAbsa.objects.bulk_create(objs, batch_size=500)
        print(f"[seed_data] Inserted {len(objs)} PlayerExpectationsAbsa records.")

    if not confusions_path.exists():
        print(f"[seed_data] WARNING: {confusions_path} not found, skipping PlayerExpectationsConfusions seeding.")
    else:
        df_conf = pd.read_csv(confusions_path)
        df_conf = df_conf.replace({pd.NA: None})
        records_conf = df_conf.to_dict(orient="records")

        objs_conf = [
            PlayerExpectationsConfusions(
                index=row.get("index"),
                sentence=row.get("sentence"),
                model_aspect=row.get("model_aspect"),
                gpt_aspect=row.get("gpt_aspect"),
                agreement=row.get("agreement"),
            )
            for row in records_conf
        ]
        PlayerExpectationsConfusions.objects.bulk_create(objs_conf, batch_size=500)
        print(f"[seed_data] Inserted {len(objs_conf)} PlayerExpectationsConfusions records.")


def unload_seed_data(apps, schema_editor):
    """Reverse operation for migration rollback."""
    PlayerExpectationsAbsa = apps.get_model("player_expectations", "PlayerExpectationsAbsa")
    PlayerExpectationsConfusions = apps.get_model("player_expectations", "PlayerExpectationsConfusions")

    PlayerExpectationsAbsa.objects.all().delete()
    PlayerExpectationsConfusions.objects.all().delete()
    print("[seed_data] All seeded records deleted.")


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("player_expectations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_seed_data, reverse_code=unload_seed_data),
    ]
