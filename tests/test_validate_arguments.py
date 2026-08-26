from backend.validate_arguments import is_do_valid, is_trigger_valid, validate_emoji


TRIGGER_REQUIREMENTS = {
    "contains-text": {"params": {"text": {"required": True}}},
    "reaction-added": {"params": {"emoji": {"required": True}}},
}

DO_REQUIREMENTS = {
    "send-message": {"params": {"channel": {"required": True}}},
    "react": {
        "params": {"emoji": {"required": True}},
        "inheritable": ["send_msg"],
    },
}


def test_required_trigger_param():
    ok, reason = is_trigger_valid(
        {"trigger_text": None}, "contains-text", TRIGGER_REQUIREMENTS)
    assert ok is False
    assert "trigger_text" in reason

    ok, reason = is_trigger_valid(
        {"trigger_text": "hello"}, "contains-text", TRIGGER_REQUIREMENTS)
    assert ok is True


def test_unicode_and_custom_emoji():
    assert validate_emoji("😀") is True
    assert validate_emoji("<:wave:1234567890>") is True
    assert validate_emoji("<a:wave:1234567890>") is True
    assert validate_emoji("not-an-emoji") is False
    assert validate_emoji(None) is False


def test_reaction_trigger_validates_emoji():
    ok, reason = is_trigger_valid(
        {"trigger_emoji": "not-an-emoji"}, "reaction-added", TRIGGER_REQUIREMENTS)
    assert ok is False
    assert "emoji" in reason.lower()

    ok, _ = is_trigger_valid(
        {"trigger_emoji": "😀"}, "reaction-added", TRIGGER_REQUIREMENTS)
    assert ok is True


def test_do_validates_do_emoji_not_trigger_emoji():
    variables = {"do_emoji": "😀", "trigger_emoji": None}
    ok, _ = is_do_valid(variables, "react", DO_REQUIREMENTS, "send_msg")
    assert ok is True

    variables = {"do_emoji": "nope", "trigger_emoji": "😀"}
    ok, reason = is_do_valid(variables, "react", DO_REQUIREMENTS, "send_msg")
    assert ok is False
    assert "emoji" in reason.lower()


def test_do_inheritance():
    variables = {"do_emoji": "😀"}
    ok, reason = is_do_valid(variables, "react", DO_REQUIREMENTS, "member_join")
    assert ok is False
    assert "inherit" in reason.lower()
