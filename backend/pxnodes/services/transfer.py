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


def import_project_data(project, payload, user):
    nodes_map = import_objects(payload.get("px_nodes", []),
                               lambda d: PxNode.objects.create(
                                   name=d["name"],
                                   description=d["description"],
                                   owner=user,
                                   project=project,
                               ))

    component_definitions_map = import_objects(payload.get("px_component_definitions", []),
                                               lambda d: PxComponentDefinition.objects.create(
                                                   name=d["name"],
                                                   type=d["type"],
                                                   owner=user,
                                                   project=project,
                                               ))

    components_map = import_objects(payload.get("px_component", []),
                                    lambda d: PxComponent.objects.create(
                                        node=nodes_map[d["node"]],
                                        definition=component_definitions_map[d["definition"]],
                                        value=d["value"],
                                        owner=user,
                                    ))

    key_definitions_map = import_objects(payload.get("px_key_definition", []),
                                         lambda d: PxKeyDefinition.objects.create(
                                             name=d["name"],
                                             key_type=d["key_type"],
                                             consumable=d["consumable"],
                                             fixed=d["fixed"],
                                             unique=d["unique"],
                                             owner=user,
                                         ))

    key_assignment_map = import_objects(payload.get("px_key_assignment", []),
                                        lambda d: PxKeyAssignment.objects.create(
                                            count=d["count"],
                                            node=nodes_map[d["node"]],
                                            definition=key_definitions_map[d["definition"]],
                                            owner=user,
                                        ))

    lock_definitions = payload.get("px_lock_definition", [])

    lock_definition_map = import_objects(lock_definitions,
                                         lambda d: PxLockDefinition.objects.create(
                                             name=d["name"],
                                             soft_gate=d["soft_gate"],
                                             unlock_mode=d["unlock_mode"],
                                             owner=user,
                                         ))

    for d in lock_definitions:
        lock = lock_definition_map[d["id"]]

        lock.unlocked_by.set([
            key_definitions_map[old_key_id]
            for old_key_id in d.get("unlocked_by", [])
        ])

    return nodes_map


def import_objects(data_list, create_fn):
    obj_map = {}

    for data in data_list:
        old_id = data["id"]
        obj = create_fn(data)
        obj_map[old_id] = obj

    return obj_map
