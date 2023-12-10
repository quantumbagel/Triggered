import importlib
import json
import ValidateTriggerDo


def get_trigger_do():
    imported_trigger = json.load(open('configuration/requirements.json'))['triggers']
    trigger_requirements = imported_trigger.copy()
    valid = ValidateTriggerDo.validate(json.load(open('configuration/requirements.json')))
    if valid:
        return valid, None
    for item in imported_trigger.keys():
        module = importlib.import_module("actions.triggers."+imported_trigger[item]['class'])
        trigger_requirements[item]['class'] = getattr(module, imported_trigger[item]['class'])

    imported_do = json.load(open('configuration/requirements.json'))['do']
    do_requirements = imported_do.copy()

    for item in imported_do.keys():
        module = importlib.import_module("actions.dos."+imported_do[item]['class'])
        do_requirements[item]['class'] = getattr(module, imported_do[item]['class'])
    return trigger_requirements, do_requirements
