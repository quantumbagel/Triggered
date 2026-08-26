from backend.duration import parse_duration_seconds, validate_duration


def test_parse_bare_seconds():
    assert parse_duration_seconds("60") == 60
    assert parse_duration_seconds(" 15 ") == 15


def test_parse_shorthand():
    assert parse_duration_seconds("60s") == 60
    assert parse_duration_seconds("5m") == 300
    assert parse_duration_seconds("1h") == 3600
    assert parse_duration_seconds("2d") == 172800
    assert parse_duration_seconds("1 H") == 3600


def test_parse_invalid():
    assert parse_duration_seconds(None) is None
    assert parse_duration_seconds("") is None
    assert parse_duration_seconds("nope") is None
    assert parse_duration_seconds("-5") is None
    assert parse_duration_seconds("1w") is None


def test_validate_duration_bounds():
    spec = {"min_seconds": 15, "max_seconds": 3600}
    ok, _ = validate_duration("1m", spec)
    assert ok is True
    ok, reason = validate_duration("5s", spec)
    assert ok is False
    assert "at least" in reason
    ok, reason = validate_duration("2h", spec)
    assert ok is False
    assert "at most" in reason
    ok, reason = validate_duration("banana", spec)
    assert ok is False
    assert "Invalid duration" in reason
