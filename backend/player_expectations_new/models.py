from django.db import models


# -------------------------------------------------------
# thesis_dataset
# -------------------------------------------------------
class ThesisDataset(models.Model):
    recommendation_id = models.TextField(db_index=True)
    app_id = models.IntegerField(null=True, blank=True, db_index=True)
    language = models.TextField(null=True, blank=True)
    review_text = models.TextField(null=True, blank=True)
    timestamp_created = models.IntegerField(null=True, blank=True, db_index=True)
    voted_up = models.IntegerField(null=True, blank=True, db_index=True)
    votes_up = models.IntegerField(null=True, blank=True)
    weighted_vote_score = models.TextField(null=True, blank=True)
    review_text_en = models.TextField(null=True, blank=True)
    votes_funny = models.IntegerField(null=True, blank=True)
    written_during_early_access = models.IntegerField(null=True, blank=True)
    received_for_free = models.IntegerField(null=True, blank=True)
    num_reviews = models.IntegerField(null=True, blank=True)
    playtime_forever = models.IntegerField(null=True, blank=True)
    playtime_at_review = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "thesis_dataset"
        managed = True
        indexes = [
            models.Index(fields=["recommendation_id"], name="idx_td_rec_id"),
            models.Index(fields=["app_id"], name="idx_td_app_id"),
            models.Index(fields=["timestamp_created"], name="idx_td_ts_created"),
            models.Index(fields=["voted_up"], name="idx_td_voted_up"),
        ]


# -------------------------------------------------------
# review_quotes
# -------------------------------------------------------
class ReviewQuotes(models.Model):
    quote_id = models.BigAutoField(primary_key=True)
    recommendation_id = models.TextField(null=True, blank=True, db_index=True)
    app_id = models.IntegerField(null=True, blank=True, db_index=True)
    game_name = models.TextField(null=True, blank=True)
    coarse_category = models.TextField(null=True, blank=True)
    quote_text = models.TextField(null=True, blank=True)
    created_at = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "review_quotes"
        managed = True
        indexes = [
            models.Index(fields=["recommendation_id"], name="idx_rq_rec_id"),
            models.Index(fields=["app_id"], name="idx_rq_app_id"),
        ]


# -------------------------------------------------------
# review_locator
# -------------------------------------------------------
class ReviewLocator(models.Model):
    recommendation_id = models.TextField(primary_key=True)
    raw_json = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    updated_at = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "review_locator"
        managed = True


# -------------------------------------------------------
# quote_code_sentiment
# -------------------------------------------------------
class QuoteCodeSentiment(models.Model):
    quote_id = models.IntegerField()
    code_int = models.IntegerField()
    coarse_category = models.TextField()

    sentiment = models.TextField(null=True, blank=True)
    raw_specialist_json = models.TextField(null=True, blank=True)
    raw_sentiment_json = models.TextField(null=True, blank=True)
    updated_at = models.IntegerField(null=True, blank=True)

    sentiment_v2 = models.TextField(null=True, blank=True)
    raw_sentiment_v2_json = models.TextField(null=True, blank=True)
    updated_at_v2 = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = "quote_code_sentiment"
        managed = True

        # SQLite composite PK workaround
        unique_together = (("quote_id", "coarse_category", "code_int"),)

        indexes = [
            models.Index(
                fields=["coarse_category", "code_int"],
                name="idx_qcs_coarse_code",
            ),
        ]