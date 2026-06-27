def import_objects(data_list, create_fn):
    obj_map = {}

    for data in data_list:
        old_id = data["id"]
        obj = create_fn(data)
        obj_map[old_id] = obj

    return obj_map
