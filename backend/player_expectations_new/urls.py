# backend/player_expectations_new/urls.py
# maps incoming HTTP paths to Python view functions.

from django.urls import path

from player_expectations_new.dataset_explorer.views import dataset_explorer_reviews
from player_expectations_new.dashboard.views import (
    compare_kpis,
    compare_sentiment_distribution,
    compare_timeseries,
    compare_top_codes,
    compare_heatmap_codes,
)

app_name = "player_expectations_new"

urlpatterns = [
    # Dataset explorer
    path("dataset-explorer/reviews/", dataset_explorer_reviews, name="dataset_explorer_reviews"),

    # Dashboard compare
    path("dashboard/compare/kpis/", compare_kpis, name="compare_kpis"),
    path("dashboard/compare/sentiments/", compare_sentiment_distribution, name="compare_sentiments"),
    path("dashboard/compare/timeseries/", compare_timeseries, name="compare_timeseries"),
    path("dashboard/compare/top-codes/", compare_top_codes, name="compare_top_codes"),
    path("dashboard/compare/heatmap-codes/", compare_heatmap_codes, name="compare_heatmap_codes"),
]
