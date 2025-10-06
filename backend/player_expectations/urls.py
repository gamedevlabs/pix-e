from django.urls import path

from .views import (
    aspect_frequency_view,
    aspect_sentiment_view,
    trend_over_time_view,
    sentiment_pie_view,
    heatmap_view,
    top_confusions_view,
    SentimentData,
)

urlpatterns = [
    path("api/aspect-frequency/", aspect_frequency_view, name="aspect-frequency"),
    path("api/aspect-sentiment/", aspect_sentiment_view, name="aspect-sentiment"),
    path("api/trend-over-time/", trend_over_time_view, name="trend-over-time"),
    path("api/sentiment-pie/", sentiment_pie_view, name="sentiment-pie"),
    path("api/heatmap/", heatmap_view, name="heatmap"),
    path("api/top-confusions/", top_confusions_view, name="top-confusions"),
    path("api/sentiments/", SentimentData.as_view(), name="sentiment-data"),
]
