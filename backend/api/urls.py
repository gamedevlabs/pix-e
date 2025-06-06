"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from llm.views import (
    MoodboardStartView,
    MoodboardGenerateView,
    MoodboardGetView,
    MoodboardEndView,
    MoodboardSuggestView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/moodboard/start/", MoodboardStartView.as_view(), name="moodboard_start"),
    path("api/moodboard/generate/", MoodboardGenerateView.as_view(), name="moodboard_generate"),
    path("api/moodboard/<uuid:session_id>/", MoodboardGetView.as_view(), name="moodboard_get"),
    path("api/moodboard/end/", MoodboardEndView.as_view(), name="moodboard_end"),
    path("api/moodboard/suggest/", MoodboardSuggestView.as_view(), name="moodboard-suggest"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
