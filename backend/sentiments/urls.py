from django.urls import path
from .views import SentimentData

urlpatterns = [
    path('sentiments/', SentimentData.as_view(), name='sentiment-data'),
]
