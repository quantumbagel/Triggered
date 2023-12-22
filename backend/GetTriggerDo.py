import importlib
import json
import backend.ValidateTriggerDo


def get_trigger_do():
    f_obj = json.load(open('configuration/requirements.json'))
    imported_trigger = f_obj['triggers']
    trigger_requirements = imported_trigger.copy()
    valid = backend.ValidateTriggerDo.validate(f_obj)
    if valid:
        return valid, None
    for item in imported_trigger.keys():
        module = importlib.import_module("actions.triggers." + imported_trigger[item]['class'])
        trigger_requirements[item]['class'] = getattr(module, imported_trigger[item]['class'])

    imported_do = f_obj['do']
    do_requirements = imported_do.copy()

    for item in imported_do.keys():
        module = importlib.import_module("actions.dos." + imported_do[item]['class'])
        do_requirements[item]['class'] = getattr(module, imported_do[item]['class'])
    return trigger_requirements, do_requirements
