import os


ENV_OVERRIDES = {
    "TRIGGERED_BOT_SECRET": ("bot_secret", str),
    "TRIGGERED_MONGODB_URI": ("mongodb_uri", str),
    "TRIGGERED_OWNER_ID": ("owner_id", int),
    "TRIGGERED_MAX_DOS_PER_TRIGGER": ("max_dos_per_trigger", int),
    "TRIGGERED_ARGUMENT_LENGTH_LIMIT": ("argument_length_limit", int),
    "TRIGGERED_ALLOWED_EXECUTION": ("allowed_execution", int),
}


def apply_env_overrides(config_dictionary: dict) -> dict:
    """Overlay TRIGGERED_* env vars onto the config dict."""
    updated = dict(config_dictionary)
    for env_name, (key, caster) in ENV_OVERRIDES.items():
        raw = os.environ.get(env_name)
        if raw is None or raw == "":
            continue
        updated[key] = caster(raw)
    return updated


def validate_config(config_dictionary: dict) -> tuple[bool, str]:
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
                     "mongodb_uri": str,
                     }

    for key in required_keys:
        if key not in config_dictionary:
            return False, f"Configuration argument \"{key}\" is not present!"
        if type(config_dictionary[key]) is not required_keys[key]:
            return False, (f"Configuration argument \"{key}\" is not correct type"
                           f" (got=\"{type(config_dictionary[key])}\", expected=\"{required_keys[key]}\")!")

    return True, ""
