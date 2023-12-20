def validate_config(config_dictionary: dict) -> (bool, str):
    """
    Validate the configuration file.
    :param config_dictionary: The configuration dictionary
    :return: Whether the given configuration is valid and the reason why.
    """
    required_keys = {"bot_secret": str,
                     "max_dos_per_trigger": int,
                     "argument_length_limit": int,
                     "allowed_execution": int,
                     "owner_id": int,
                     "mongodb_uri": str}
    for key in required_keys:
        if key not in config_dictionary:
            return False, f"Configuration argument \"{key}\" is not present!"
        if type(config_dictionary[key]) is not required_keys[key]:
            return False, (f"Configuration argument \"{key}\" is not correct type"
                           f" (got=\"{type(config_dictionary[key])}\", expected=\"{required_keys[key]}\")!")

    return True, ""

