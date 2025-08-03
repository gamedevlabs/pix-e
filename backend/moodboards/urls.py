from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MoodboardViewSet,
    MoodboardImageViewSet,
    MoodboardCommentViewSet,
    MoodboardTemplateViewSet,
    MoodboardAIViewSet,
)

# Create the main router
router = DefaultRouter()
router.register(r'moodboards', MoodboardViewSet, basename='moodboard')
router.register(r'templates', MoodboardTemplateViewSet, basename='moodboardtemplate')
router.register(r'moodboard-ai', MoodboardAIViewSet, basename='moodboard-ai')

app_name = 'moodboards'

urlpatterns = [
    # Include all router URLs
    path('api/', include(router.urls)),
    
    # Manual nested URLs for moodboard images
    path('api/moodboards/<uuid:moodboard_pk>/images/', 
         MoodboardImageViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='moodboard-images-list'),
    path('api/moodboards/<uuid:moodboard_pk>/images/bulk-action/', 
         MoodboardImageViewSet.as_view({'post': 'bulk_action'}), 
         name='moodboard-images-bulk-action'),
    path('api/moodboards/<uuid:moodboard_pk>/images/<uuid:pk>/', 
         MoodboardImageViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='moodboard-images-detail'),
    
    # Manual nested URLs for moodboard comments
    path('api/moodboards/<uuid:moodboard_pk>/comments/', 
         MoodboardCommentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='moodboard-comments-list'),
    path('api/moodboards/<uuid:moodboard_pk>/comments/<uuid:pk>/', 
         MoodboardCommentViewSet.as_view({
             'get': 'retrieve', 
             'put': 'update', 
             'patch': 'partial_update', 
             'delete': 'destroy'
         }), 
         name='moodboard-comments-detail'),
]
