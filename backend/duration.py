import re

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_DURATION_RE = re.compile(r"^(\d+)\s*([smhd])$")


def parse_duration_seconds(text: str | None) -> int | None:
    """
    Parse a duration as seconds.

    Accepts a bare integer (seconds) or shorthand: 60s, 5m, 1h, 1d.
    """
    if not text or not isinstance(text, str):
        return None
    raw = text.strip().lower()
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)
    match = _DURATION_RE.fullmatch(raw)
    if not match:
        return None
    return int(match.group(1)) * _UNITS[match.group(2)]


def validate_duration(value: str, spec: dict) -> tuple[bool, str]:
    """Return whether a duration string satisfies min/max bounds from a param spec."""
    seconds = parse_duration_seconds(value)
    if seconds is None:
        return False, "Invalid duration! Use seconds or shorthand like 60s, 5m, 1h, 1d."
    min_seconds = spec.get("min_seconds")
    max_seconds = spec.get("max_seconds")
    if min_seconds is not None and seconds < min_seconds:
        return False, f"Duration must be at least {min_seconds} seconds."
    if max_seconds is not None and seconds > max_seconds:
        return False, f"Duration must be at most {max_seconds} seconds."
    return True, ""
