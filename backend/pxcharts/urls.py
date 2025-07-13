from rest_framework_nested import routers

from .views import PxChartEdgeViewSet, PxChartNodeViewSet, PxChartViewSet

router = routers.SimpleRouter()
router.register(r"pxcharts", PxChartViewSet, basename="pxcharts")

charts_router = routers.NestedSimpleRouter(router, r"pxcharts", lookup="px_chart")
charts_router.register(r"pxedges", PxChartEdgeViewSet, basename="px_chart_edge")
charts_router.register(r"pxnodes", PxChartNodeViewSet, basename="px_chart_node")

urlpatterns = router.urls + charts_router.urls
