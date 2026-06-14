from django.contrib import admin

from .models import (
    PxComponent,
    PxComponentDefinition,
    PxKeyAssignment,
    PxKeyDefinition,
    PxLockDefinition,
    PxNode,
)

admin.site.register(PxNode)
admin.site.register(PxComponent)
admin.site.register(PxComponentDefinition)
admin.site.register(PxKeyDefinition)
admin.site.register(PxKeyAssignment)
admin.site.register(PxLockDefinition)
