from django.urls import path

from .views import ExportDataView, ImportDataView

urlpatterns = [
    path("pxexport/", ExportDataView.as_view(), name="pxexports-pxdata"),
    path("pximport/", ImportDataView.as_view(), name="pximports-pxdata"),
]
