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
    for param in requirements[trigger]['params'].keys():
        if requirements[trigger]['params'][param]['required'] and variables['trigger_' + param] is None:
            return False, f"trigger_{param} is required and not provided!"
        if param == 'emoji':
            if not validate_emoji(variables['trigger_emoji']):
                return False, "Invalid emoji!"

    return True, ""


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
        for param in requirements[do]['params'].keys():
            if requirements[do]['params'][param]['required'] and variables['do_' + param] is None:
                return False, f"do_{param} is required and not provided!"
            if param == 'emoji':
                if not validate_emoji(variables['trigger_emoji']):
                    return False, "Invalid emoji!"
    if 'inheritable' in requirements[do].keys() and trigger_type not in requirements[do]['inheritable']:
        return False, (f"Do cannot inherit from \"{trigger_type}.\"\n"
                       f"It can only inherit from these types: {','.join(requirements[do]['inheritable'])}")

    return True, ""


from emoji import EMOJI_DATA as EMOJIS

new_emoji = {}
for emoji in EMOJIS.keys():
    if 'alias' in EMOJIS[emoji].keys():
        new_emoji.update({emoji: EMOJIS[emoji]['alias'][0]})
    else:
        new_emoji.update({emoji: EMOJIS[emoji]['en']})


def validate_emoji(emoji_name):
    """
    Validate an emoji using the emoji library
    :param emoji_name: The emoji
    :return: Whether the emoji is valid.
    """
    return emoji_name in new_emoji.keys()
