import json

from backend.validate_trigger_do import load_action_class, validate


def get_trigger_do():
    f_obj = json.load(open("configuration/requirements.json"))
    imported_trigger = f_obj["triggers"]
    trigger_requirements = imported_trigger.copy()
    valid = validate(f_obj)
    if valid:
        return valid, None
    for item in imported_trigger.keys():
        trigger_requirements[item]["class"] = load_action_class("triggers", item, imported_trigger[item])

    imported_do = f_obj["do"]
    do_requirements = imported_do.copy()

    for item in imported_do.keys():
        do_requirements[item]["class"] = load_action_class("dos", item, imported_do[item])
    return trigger_requirements, do_requirements
