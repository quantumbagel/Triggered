"""Access-list helpers for server and user white/blacklists."""


def normalize_mode(mode: str | None) -> str | None:
    """Return whitelist/blacklist in lowercase, or None if missing."""
    if mode is None:
        return None
    lowered = str(mode).strip().lower()
    if lowered in ("whitelist", "blacklist"):
        return lowered
    return None


def item_is_denied(encoded_item, access_list: dict | None, *, default_allow: bool) -> bool:
    """
    Return True if this encoded Discord object is blocked by the access list.

    None items are skipped (not denied). A missing list uses default_allow.
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
    """Return True if any non-None item in encoded_items is denied."""
    return any(
        item_is_denied(item, access_list, default_allow=default_allow)
        for item in encoded_items
        if item is not None
    )
