from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("player_expectations_new", "0002_seed_data"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS idx_qcs_coarse_code_sentv2
            ON quote_code_sentiment(coarse_category, code_int)
            WHERE sentiment_v2 IS NOT NULL AND sentiment_v2 <> '';
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_qcs_coarse_code_sentv2;",
        )
    ]