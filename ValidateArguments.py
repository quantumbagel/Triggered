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


def is_do_valid(variables: dict, do: str, requirements: dict):
    """
    Returns whether this should be allowed
    :param requirements: the do requirements
    :param do: the do action
    :param variables: the variables
    :return: a bool and the reason
    """
    for param in requirements[do]['params'].keys():
        if requirements[do]['params'][param]['required'] and variables['do_' + param] is None:
            return False, f"do_{param} is required and not provided!"
        if param == 'emoji':
            if not validate_emoji(variables['trigger_emoji']):
                return False, "Invalid emoji!"
    return True, ""


from emoji import EMOJI_DATA as EMOJIS

new_emoji = {}
for emoji in EMOJIS.keys():
    if 'alias' in EMOJIS[emoji].keys():
        new_emoji.update({emoji: EMOJIS[emoji]['alias'][0]})
    else:
        new_emoji.update({emoji: EMOJIS[emoji]['en']})


def validate_emoji(emoji_name):
    return emoji_name in new_emoji.keys()
