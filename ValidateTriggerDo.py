import importlib
import actions.dos.Do
import actions.triggers.Trigger
valid_type_names = ['send_msg', 'vc_join', 'vc_leave', 'reaction_add', 'reaction_remove', 'member_join', 'member_leave']


def validate(data):
    trigger_req = data['triggers']
    do_req = data['do']
    for item in trigger_req.keys():
        try:
            module = importlib.import_module("actions.triggers." + trigger_req[item]['class'])
            check_against = getattr(module, trigger_req[item]['class'])
            if not issubclass(check_against, actions.triggers.Trigger.Trigger):
                return f"Failed to validate (Trigger {item} does not inherit from actions.triggers.Trigger.Trigger)"
        except ImportError:
            return f"Failed to validate (Invalid class at root/triggers/{item}/class with val={trigger_req[item]['class']})"
        if trigger_req[item]['type'] not in valid_type_names:
            return f"Failed to validate type of trigger (got={trigger_req[item]['type']})"
    for item in do_req.keys():
        try:
            module = importlib.import_module("actions.dos." + do_req[item]['class'])
            check_against = getattr(module, do_req[item]['class'])
            if not issubclass(check_against, actions.dos.Do.Do):
                return f"Failed to validate (Do {item} does not inherit from actions.dos.Do.Do)"
        except ImportError:
            return f"Failed to validate (Invalid class at root/do/{item}/class with val={do_req[item]['class']})"
    return ""
