from django.contrib import admin

from pxcharts.models import PxChart, PxChartContainer, PxChartEdge

admin.site.register(PxChart)
admin.site.register(PxChartContainer)
admin.site.register(PxChartEdge)
