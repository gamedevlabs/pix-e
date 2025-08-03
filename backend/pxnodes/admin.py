from django.contrib import admin

from .models import PxComponent, PxComponentDefinition, PxNode

admin.site.register(PxNode)
admin.site.register(PxComponent)
admin.site.register(PxComponentDefinition)
