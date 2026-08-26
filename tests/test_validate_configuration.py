from backend.validate_configuration import apply_env_overrides, validate_config


VALID = {
    "bot_secret": "token",
    "max_dos_per_trigger": 3,
    "argument_length_limit": 128,
    "allowed_execution": 3,
    "owner_id": 1,
    "mongodb_uri": "mongodb://localhost:27017",
}


def test_valid_config():
    ok, reason = validate_config(VALID)
    assert ok is True
    assert reason == ""


def test_missing_key():
    data = dict(VALID)
    del data["owner_id"]
    ok, reason = validate_config(data)
    assert ok is False
    assert "owner_id" in reason


def test_wrong_type():
    data = dict(VALID)
    data["owner_id"] = "yes"
    ok, reason = validate_config(data)
    assert ok is False


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("TRIGGERED_BOT_SECRET", "from-env")
    monkeypatch.setenv("TRIGGERED_OWNER_ID", "99")
    monkeypatch.setenv("TRIGGERED_MONGODB_URI", "mongodb://mongo:27017")
    updated = apply_env_overrides(VALID)
    assert updated["bot_secret"] == "from-env"
    assert updated["owner_id"] == 99
    assert updated["mongodb_uri"] == "mongodb://mongo:27017"
    assert VALID["bot_secret"] == "token"


def test_env_overrides_ignore_empty(monkeypatch):
    monkeypatch.setenv("TRIGGERED_BOT_SECRET", "")
    updated = apply_env_overrides(VALID)
    assert updated["bot_secret"] == "token"
