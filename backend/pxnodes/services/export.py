from pxnodes.export_serializers import PxNodeSerializer, PxComponentSerializer, PxComponentDefinitionSerializer, \
    PxKeyDefinitionSerializer, PxKeyAssignmentSerializer, PxLockDefinitionSerializer
from pxnodes.models import PxNode, PxComponentDefinition, PxComponent, PxKeyDefinition, PxKeyAssignment, \
    PxLockDefinition


def export_project_data(project):
    px_nodes = PxNode.objects.filter(project=project)

    px_component_definitions = PxComponentDefinition.objects.filter(project=project)
    px_component = PxComponent.objects.filter(
        node__in=px_nodes
    )
    px_key_definition = PxKeyDefinition.objects.filter(owner=project.user)
    px_key_assignment = PxKeyAssignment.objects.filter(owner=project.user)
    px_lock_definition = PxLockDefinition.objects.filter(owner=project.user)

    return {
        "px_nodes": PxNodeSerializer(px_nodes, many=True).data,
        "px_component_definitions": PxComponentDefinitionSerializer(px_component_definitions, many=True).data,
        "px_component": PxComponentSerializer(px_component, many=True).data,
        "px_key_definition": PxKeyDefinitionSerializer(px_key_definition, many=True).data,
        "px_key_assignment": PxKeyAssignmentSerializer(px_key_assignment, many=True).data,
        "px_lock_definition": PxLockDefinitionSerializer(px_lock_definition, many=True).data,
    }