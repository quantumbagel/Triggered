import json

from backend.validate_trigger_do import action_module_name, validate


def test_bundled_requirements_are_valid():
    with open("configuration/requirements.json") as handle:
        data = json.load(handle)
    assert validate(data) == ""


def test_rejects_unknown_trigger_type():
    with open("configuration/requirements.json") as handle:
        data = json.load(handle)
    first = next(iter(data["triggers"]))
    data["triggers"][first]["type"] = "not-a-real-type"
    assert "Failed to validate type" in validate(data)


def test_action_module_name_uses_id_or_override():
    assert action_module_name("contains-text", {}) == "contains_text"
    assert action_module_name("contains-text", {"module": "custom"}) == "custom"


def test_bundled_requirements_load_classes():
    from backend.get_trigger_do import get_trigger_do
    from actions.triggers.contains_text import ContainsTextTrigger
    from actions.triggers.user_mentioned import UserMentionedTrigger
    from actions.dos.send_message import SendMessageDo
    from actions.dos.add_reaction import AddReactionDo

    triggers, dos = get_trigger_do()
    assert dos is not None
    assert triggers["contains-text"]["class"] is ContainsTextTrigger
    assert triggers["user-mentioned"]["class"] is UserMentionedTrigger
    assert dos["send-message"]["class"] is SendMessageDo
    assert dos["add-reaction"]["class"] is AddReactionDo
    assert dos["add-reaction"]["inheritable"] == ["send_msg"]
