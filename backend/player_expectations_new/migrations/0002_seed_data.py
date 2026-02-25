from django.db import migrations
import pandas as pd
from pathlib import Path


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # normalize missing values to None
    df = df.where(pd.notnull(df), None)
    return df


def load_seed_data(apps, schema_editor):
    ThesisDataset = apps.get_model("player_expectations_new", "ThesisDataset")
    ReviewQuotes = apps.get_model("player_expectations_new", "ReviewQuotes")
    QuoteCodeSentiment = apps.get_model("player_expectations_new", "QuoteCodeSentiment")
    ReviewLocator = apps.get_model("player_expectations_new", "ReviewLocator")

    base_dir = Path(__file__).resolve().parent.parent
    seeds_dir = base_dir / "seeds"

    thesis_path = seeds_dir / "thesis_dataset.csv"
    quotes_path = seeds_dir / "review_quotes.csv"
    qcs_path = seeds_dir / "quote_code_sentiment.csv"
    locator_path = seeds_dir / "review_locator.csv"

    # ---- thesis_dataset ----
    if thesis_path.exists():
        df = _read_csv(thesis_path)
        objs = [
            ThesisDataset(
                recommendation_id=r.get("recommendation_id"),
                app_id=r.get("app_id"),
                language=r.get("language"),
                review_text=r.get("review_text"),
                timestamp_created=r.get("timestamp_created"),
                voted_up=r.get("voted_up"),
                votes_up=r.get("votes_up"),
                weighted_vote_score=r.get("weighted_vote_score"),
                review_text_en=r.get("review_text_en"),
                votes_funny=r.get("votes_funny"),
                written_during_early_access=r.get("written_during_early_access"),
                received_for_free=r.get("received_for_free"),
                num_reviews=r.get("num_reviews"),
                playtime_forever=r.get("playtime_forever"),
                playtime_at_review=r.get("playtime_at_review"),
            )
            for r in df.to_dict(orient="records")
        ]
        ThesisDataset.objects.bulk_create(objs, batch_size=2000)
        print(f"[seed] thesis_dataset inserted: {len(objs)}")
    else:
        print(f"[seed] WARNING missing: {thesis_path}")

    # ---- review_quotes ----
    if quotes_path.exists():
        df = _read_csv(quotes_path)
        objs = [
            ReviewQuotes(
                # if your CSV includes quote_id and you want to preserve it:
                quote_id=r.get("quote_id") if "quote_id" in r else None,
                recommendation_id=r.get("recommendation_id"),
                app_id=r.get("app_id"),
                game_name=r.get("game_name"),
                coarse_category=r.get("coarse_category"),
                quote_text=r.get("quote_text"),
                created_at=r.get("created_at"),
            )
            for r in df.to_dict(orient="records")
        ]
        # If quote_id is autoincrement but you are supplying ids,
        # SQLite will accept explicit values for INTEGER PRIMARY KEY.
        ReviewQuotes.objects.bulk_create(objs, batch_size=2000)
        print(f"[seed] review_quotes inserted: {len(objs)}")
    else:
        print(f"[seed] WARNING missing: {quotes_path}")

    # ---- quote_code_sentiment ----
    if qcs_path.exists():
        df = _read_csv(qcs_path)
        objs = [
            QuoteCodeSentiment(
                quote_id=r.get("quote_id"),
                code_int=r.get("code_int"),
                coarse_category=r.get("coarse_category"),
                sentiment=r.get("sentiment"),
                raw_specialist_json=r.get("raw_specialist_json"),
                raw_sentiment_json=r.get("raw_sentiment_json"),
                updated_at=r.get("updated_at"),
                sentiment_v2=r.get("sentiment_v2"),
                raw_sentiment_v2_json=r.get("raw_sentiment_v2_json"),
                updated_at_v2=r.get("updated_at_v2"),
            )
            for r in df.to_dict(orient="records")
        ]
        QuoteCodeSentiment.objects.bulk_create(objs, batch_size=4000, ignore_conflicts=True)
        print(f"[seed] quote_code_sentiment inserted: {len(objs)} (ignore_conflicts=True)")
    else:
        print(f"[seed] WARNING missing: {qcs_path}")

    # ---- review_locator ----
    if locator_path.exists():
        df = _read_csv(locator_path)
        objs = [
            ReviewLocator(
                recommendation_id=r.get("recommendation_id"),
                raw_json=r.get("raw_json"),
                status=r.get("status"),
                updated_at=r.get("updated_at"),
            )
            for r in df.to_dict(orient="records")
        ]
        ReviewLocator.objects.bulk_create(objs, batch_size=2000, ignore_conflicts=True)
        print(f"[seed] review_locator inserted: {len(objs)}")
    else:
        print(f"[seed] WARNING missing: {locator_path}")


def unload_seed_data(apps, schema_editor):
    ThesisDataset = apps.get_model("player_expectations_new", "ThesisDataset")
    ReviewQuotes = apps.get_model("player_expectations_new", "ReviewQuotes")
    QuoteCodeSentiment = apps.get_model("player_expectations_new", "QuoteCodeSentiment")
    ReviewLocator = apps.get_model("player_expectations_new", "ReviewLocator")

    ThesisDataset.objects.all().delete()
    ReviewQuotes.objects.all().delete()
    QuoteCodeSentiment.objects.all().delete()
    ReviewLocator.objects.all().delete()
    print("[seed] deleted all seeded data")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("player_expectations_new", "0001_initial")]
    operations = [migrations.RunPython(load_seed_data, reverse_code=unload_seed_data)]