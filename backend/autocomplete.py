"""Filter helpers for Discord slash-command autocomplete (25-result cap)."""

MAX_RESULTS = 25


def filter_autocomplete(current: str, items: list[tuple[str, str]], *,
                        limit: int = MAX_RESULTS) -> list[tuple[str, str]]:
    """
    Return (label, value) pairs matching current, ranked and capped.

    Matches against the visible name and the submitted id. Prefix matches
    rank above substring matches so typing still finds items past the cap.
    """
    needle = (current or "").strip().lower()
    matched: list[tuple[int, str, str]] = []
    seen_names: set[str] = set()
    for label, value in items:
        if not label or not value:
            continue
        label_l = label.lower()
        value_l = value.lower()
        compact = f"{label_l} {value_l}".replace("-", " ").replace("_", " ")
        if needle and needle not in compact and needle not in label_l and needle not in value_l:
            continue
        name = label
        if name in seen_names:
            name = f"{label} ({value})"
        if len(name) > 100:
            name = name[:100]
        if name in seen_names:
            continue
        seen_names.add(name)
        prefix = bool(needle) and (label_l.startswith(needle) or value_l.startswith(needle))
        matched.append((0 if prefix or not needle else 1, name, value))
    matched.sort(key=lambda row: (row[0], row[1].lower()))
    return [(name, value) for _rank, name, value in matched[:limit]]
