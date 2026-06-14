"""
URL patterns for PxNodes LLM operations.

Mounted at /llm/nodes/ in main urls.py
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from pxnodes.llm.agents.change_propagation.views import ChangePropagationView
from pxnodes.llm.agents.consistency.views import ConsistencyCheckView
from pxnodes.llm_views import NodeFeedbackView

app_name = "pxnodes_llm"

router = DefaultRouter()
router.register(r"nodes", NodeFeedbackView, basename="node-feedback")

urlpatterns = router.urls + [
    path(
        "consistency/check/",
        ConsistencyCheckView.as_view(),
        name="consistency-check",
    ),
    path(
        "propagation/check/",
        ChangePropagationView.as_view(),
        name="propagation-check",
    ),
]
