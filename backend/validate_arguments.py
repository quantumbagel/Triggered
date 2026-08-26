import re

from emoji import EMOJI_DATA as EMOJIS

from backend.duration import validate_duration

CUSTOM_EMOJI_RE = re.compile(r"^<a?:\w+:\d+>$")


def _check_params(variables: dict, params: dict, prefix: str) -> tuple[bool, str]:
    for param, spec in params.items():
        value = variables.get(f"{prefix}_{param}")
        if spec.get("required") and value is None:
            return False, f"{prefix}_{param} is required and not provided!"
        if param == "emoji" and value is not None and not validate_emoji(value):
            return False, "Invalid emoji!"
        if spec.get("format") == "duration" and value is not None:
            ok, reason = validate_duration(value, spec)
            if not ok:
                return False, reason
    return True, ""


def is_trigger_valid(variables: dict, trigger: str, requirements: dict):
    """
    Returns whether this should be allowed
    :param requirements: the requirements of the trigger
    :param variables: the variables
    :param trigger: the name of the trigger
    :return: a bool and the reason
    """
    if 'params' not in requirements[trigger].keys():
        return True, ""  # No stated requirements
    return _check_params(variables, requirements[trigger]["params"], "trigger")


def is_do_valid(variables: dict, do: str, requirements: dict, trigger_type: str):
    """
    Returns whether this should be allowed
    :param requirements: the do requirements
    :param do: the do action
    :param variables: the variables
    :param trigger_type: The type of the trigger
    :return: a bool and the reason
    """
    if 'params' in requirements[do].keys():
        ok, reason = _check_params(variables, requirements[do]["params"], "do")
        if not ok:
            return False, reason
    if 'inheritable' in requirements[do].keys() and trigger_type not in requirements[do]['inheritable']:
        return False, (f"Do cannot inherit from \"{trigger_type}.\"\n"
                       f"It can only inherit from these types: {','.join(requirements[do]['inheritable'])}")

    return True, ""


def validate_emoji(emoji_name):
    """
    Validate a unicode emoji or a Discord custom emoji (<:name:id> / <a:name:id>).
    :param emoji_name: The emoji
    :return: Whether the emoji is valid.
    """
    if not emoji_name or not isinstance(emoji_name, str):
        return False
    if emoji_name in EMOJIS:
        return True
    return CUSTOM_EMOJI_RE.match(emoji_name) is not None
