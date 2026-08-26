from backend.permissions import any_item_denied, item_is_denied, normalize_mode


def test_normalize_mode_accepts_mixed_case():
    assert normalize_mode("Whitelist") == "whitelist"
    assert normalize_mode("BLACKLIST") == "blacklist"
    assert normalize_mode("  whitelist  ") == "whitelist"
    assert normalize_mode("nope") is None
    assert normalize_mode(None) is None


def test_missing_server_list_allows():
    assert item_is_denied(["channel", 1], None, default_allow=True) is False


def test_missing_user_list_denies():
    assert item_is_denied(["member", 1], None, default_allow=False) is True


def test_none_items_are_skipped():
    access = {"mode": "whitelist", "value": [["channel", 1]]}
    assert item_is_denied(None, access, default_allow=True) is False
    assert any_item_denied([None, None], access, default_allow=True) is False


def test_whitelist_and_blacklist():
    access = {"mode": "Whitelist", "value": [["channel", 1]]}
    assert item_is_denied(["channel", 1], access, default_allow=True) is False
    assert item_is_denied(["channel", 2], access, default_allow=True) is True

    access = {"mode": "blacklist", "value": [["channel", 1]]}
    assert item_is_denied(["channel", 1], access, default_allow=True) is True
    assert item_is_denied(["channel", 2], access, default_allow=True) is False


def test_any_item_denied_on_mixed_list():
    access = {"mode": "blacklist", "value": [["role", 9]]}
    assert any_item_denied([None, ["role", 9]], access, default_allow=True) is True
    assert any_item_denied([None, ["role", 8]], access, default_allow=True) is False
