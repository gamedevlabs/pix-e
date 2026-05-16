from django.urls import path

from .views import HelpdeskTicketView

urlpatterns = [
    path("tickets/", HelpdeskTicketView.as_view()),
]
