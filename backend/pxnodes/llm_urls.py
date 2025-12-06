"""
URL patterns for PxNodes LLM operations.

Mounted at /llm/nodes/ in main urls.py
"""

from rest_framework.routers import DefaultRouter

from pxnodes.llm_views import NodeFeedbackView

app_name = "pxnodes_llm"

router = DefaultRouter()
router.register(r"nodes", NodeFeedbackView, basename="node-feedback")

urlpatterns = router.urls
