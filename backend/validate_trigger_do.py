import importlib

from actions.dos.do import Do
from actions.triggers.trigger import Trigger

valid_type_names = [
    "send_msg", "vc_join", "vc_leave", "reaction_add", "reaction_remove",
    "member_join", "member_leave", "message_edit", "message_delete",
    "role_add", "role_remove", "nickname_change", "member_boost", "scheduled",
]


def action_module_name(item_id: str, spec: dict) -> str:
    """Map a registry ID to a Python module name (hyphens become underscores)."""
    return spec.get("module") or item_id.replace("-", "_")


def load_action_class(kind: str, item_id: str, spec: dict):
    """Import the class registered for a trigger or do."""
    module = importlib.import_module(f"actions.{kind}.{action_module_name(item_id, spec)}")
    return getattr(module, spec["class"])


def validate(data):
    trigger_req = data["triggers"]
    do_req = data["do"]
    for item in trigger_req.keys():
        try:
            check_against = load_action_class("triggers", item, trigger_req[item])
            if not issubclass(check_against, Trigger):
                return (f"Failed to validate (Trigger {item} does not inherit from "
                        f"actions.triggers.trigger.Trigger)")
        except (ImportError, AttributeError) as err:
            return (f"Failed to validate (Invalid class at triggers/{item} "
                    f"with class={trigger_req[item].get('class')}: {err})")
        if trigger_req[item]["type"] not in valid_type_names:
            return f"Failed to validate type of trigger (got={trigger_req[item]['type']})"
    for item in do_req.keys():
        try:
            check_against = load_action_class("dos", item, do_req[item])
            if not issubclass(check_against, Do):
                return f"Failed to validate (Do {item} does not inherit from actions.dos.do.Do)"
        except (ImportError, AttributeError) as err:
            return (f"Failed to validate (Invalid class at do/{item} "
                    f"with class={do_req[item].get('class')}: {err})")
    return ""
