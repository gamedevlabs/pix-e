# -----------------------------
# SQLite performance indexes (Dataset Explorer)
# -----------------------------
SQLITE_DATASET_EXPLORER_INDEXES = [
    # thesis_dataset filters + joins
    "CREATE INDEX IF NOT EXISTS idx_td_app_id ON thesis_dataset(app_id)",
    "CREATE INDEX IF NOT EXISTS idx_td_rec_id ON thesis_dataset(recommendation_id)",
    "CREATE INDEX IF NOT EXISTS idx_td_ts_created ON thesis_dataset(timestamp_created)",
    "CREATE INDEX IF NOT EXISTS idx_td_voted_up ON thesis_dataset(voted_up)",

    # attach quotes to selected page of reviews
    "CREATE INDEX IF NOT EXISTS idx_rq_rec_id ON review_quotes(recommendation_id)",
    "CREATE INDEX IF NOT EXISTS idx_rq_app_id ON review_quotes(app_id)",

    # critical: you filter by coarse_category + code_int (PK starts with quote_id so it does NOT help)
    "CREATE INDEX IF NOT EXISTS idx_qcs_coarse_code ON quote_code_sentiment(coarse_category, code_int)",

    # optional but very effective because you always require sentiment_v2 not null/empty
    "CREATE INDEX IF NOT EXISTS idx_qcs_coarse_code_sentv2 "
    "ON quote_code_sentiment(coarse_category, code_int) "
    "WHERE sentiment_v2 IS NOT NULL AND sentiment_v2 <> ''",
]
