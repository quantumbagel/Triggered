"""Whitelist/blacklist helpers."""


def normalize_mode(mode: str | None) -> str | None:
    """Lowercase whitelist/blacklist, or None if it's missing/garbage."""
    if mode is None:
        return None
    lowered = str(mode).strip().lower()
    if lowered in ("whitelist", "blacklist"):
        return lowered
    return None


def item_is_denied(encoded_item, access_list: dict | None, *, default_allow: bool) -> bool:
    """
    True if this encoded Discord object is blocked.

    None items are skipped. A missing list uses default_allow.
    """
    if encoded_item is None:
        return False
    if access_list is None:
        return not default_allow
    mode = normalize_mode(access_list.get("mode"))
    values = access_list.get("value") or []
    if mode == "whitelist":
        return encoded_item not in values
    if mode == "blacklist":
        return encoded_item in values
    return not default_allow


def any_item_denied(encoded_items: list, access_list: dict | None, *, default_allow: bool) -> bool:
    """True if any of these items is blocked."""
    return any(
        item_is_denied(item, access_list, default_allow=default_allow)
        for item in encoded_items
        if item is not None
    )
