import os


def _as_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in ("1", "true", "yes", "on"):
        return True
    if lowered in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


ENV_OVERRIDES = {
    "TRIGGERED_BOT_SECRET": ("bot_secret", str),
    "TRIGGERED_MONGODB_URI": ("mongodb_uri", str),
    "TRIGGERED_OWNER_ID": ("owner_id", int),
    "TRIGGERED_MAX_DOS_PER_TRIGGER": ("max_dos_per_trigger", int),
    "TRIGGERED_ARGUMENT_LENGTH_LIMIT": ("argument_length_limit", int),
    "TRIGGERED_ALLOWED_EXECUTION": ("allowed_execution", int),
    "TRIGGERED_AUTO_UPDATE": ("auto_update", _as_bool),
    "TRIGGERED_CHECK_FOR_UPDATES": ("check_for_updates", _as_bool),
    "TRIGGERED_UPDATE_TO": ("update_to", str),
}


def apply_env_overrides(config_dictionary: dict) -> dict:
    """Return a copy of config with TRIGGERED_* environment variables applied."""
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
                     "auto_update": bool,
                     "update_to": str,
                     "check_for_updates": bool
                     }

    for key in required_keys:
        if key not in config_dictionary:
            return False, f"Configuration argument \"{key}\" is not present!"
        if type(config_dictionary[key]) is not required_keys[key]:
            return False, (f"Configuration argument \"{key}\" is not correct type"
                           f" (got=\"{type(config_dictionary[key])}\", expected=\"{required_keys[key]}\")!")
        if key == "update_to" and config_dictionary[key] not in ["stable", "dev", "main"]:
            return False, f"Configuration argument \"update_to\" must be \"stable\", \"dev\", or \"main.\""

    return True, ""
