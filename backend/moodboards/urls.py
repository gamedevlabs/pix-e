from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    MoodboardCanvasViewSet,
    MoodboardCommentViewSet,
    MoodboardImageViewSet,
    MoodboardTemplateViewSet,
    MoodboardTextElementViewSet,
    MoodboardViewSet,
)

# Create the main router
router = DefaultRouter()
router.register(r"moodboards", MoodboardViewSet, basename="moodboard")
router.register(r"templates", MoodboardTemplateViewSet, basename="moodboardtemplate")

app_name = "moodboards"

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    # Manual nested URLs for moodboard images
    path(
        "moodboards/<uuid:moodboard_pk>/images/",
        MoodboardImageViewSet.as_view({"get": "list", "post": "create"}),
        name="moodboard-images-list",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/images/bulk-action/",
        MoodboardImageViewSet.as_view({"post": "bulk_action"}),
        name="moodboard-images-bulk-action",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/images/<uuid:pk>/",
        MoodboardImageViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="moodboard-images-detail",
    ),
    # Image editing endpoints
    path(
        "moodboards/<uuid:moodboard_pk>/images/<uuid:pk>/edit/",
        MoodboardImageViewSet.as_view({"post": "edit_image"}),
        name="moodboard-images-edit",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/images/<uuid:pk>/preview-edit/",
        MoodboardImageViewSet.as_view({"post": "preview_edit"}),
        name="moodboard-images-preview-edit",
    ),
    # Manual nested URLs for moodboard comments
    path(
        "moodboards/<uuid:moodboard_pk>/comments/",
        MoodboardCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="moodboard-comments-list",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/comments/<uuid:pk>/",
        MoodboardCommentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="moodboard-comments-detail",
    ),
    # Manual nested URLs for moodboard text elements
    path(
        "moodboards/<uuid:moodboard_pk>/text-elements/",
        MoodboardTextElementViewSet.as_view({"get": "list", "post": "create"}),
        name="moodboard-text-elements-list",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/text-elements/<uuid:pk>/",
        MoodboardTextElementViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="moodboard-text-elements-detail",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/text-elements/bulk-update/",
        MoodboardTextElementViewSet.as_view({"post": "bulk_update"}),
        name="moodboard-text-elements-bulk-update",
    ),
    path(
        "moodboards/<uuid:moodboard_pk>/text-elements/bulk-delete/",
        MoodboardTextElementViewSet.as_view({"post": "bulk_delete"}),
        name="moodboard-text-elements-bulk-delete",
    ),
    # Canvas operations
    path(
        "moodboards/canvas/<uuid:moodboard_id>/export/",
        MoodboardCanvasViewSet.as_view({"post": "export_canvas"}),
        name="moodboard-canvas-export",
    ),
    path(
        "moodboards/canvas/<uuid:moodboard_id>/auto-layout/",
        MoodboardCanvasViewSet.as_view({"post": "auto_layout"}),
        name="moodboard-canvas-auto-layout",
    ),
    path(
        "moodboards/canvas/<uuid:moodboard_id>/import-image/",
        MoodboardCanvasViewSet.as_view({"post": "import_image"}),
        name="moodboard-canvas-import-image",
    ),
]
