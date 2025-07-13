from django.contrib import admin

from pxcharts.models import PxChart, PxChartEdge, PxChartNode

admin.site.register(PxChart)
admin.site.register(PxChartNode)
admin.site.register(PxChartEdge)
