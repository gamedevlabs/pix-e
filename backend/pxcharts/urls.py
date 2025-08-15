from rest_framework_nested import routers

from .views import PxChartContainerViewSet, PxChartEdgeViewSet, PxChartViewSet

router = routers.SimpleRouter()
router.register(r"pxcharts", PxChartViewSet, basename="pxcharts")

charts_router = routers.NestedSimpleRouter(router, r"pxcharts", lookup="px_chart")
charts_router.register(r"pxedges", PxChartEdgeViewSet, basename="px_chart_edge")
charts_router.register(
    r"pxcontainers", PxChartContainerViewSet, basename="px_chart_container"
)

urlpatterns = router.urls + charts_router.urls
