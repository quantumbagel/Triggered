import asyncio
from types import SimpleNamespace

from actions.dos.add_reaction import AddReactionDo
from actions.dos.add_role import AddRoleDo
from actions.dos.remove_role import RemoveRoleDo
from actions.dos.send_text import SendTextDo


def _run(coro):
    return asyncio.run(coro)


def test_add_role_human():
    text = _run(AddRoleDo.human({"do_role": SimpleNamespace(name="alerts")}, "member-joined"))
    assert "alerts" in text
    missing = _run(AddRoleDo.human({"do_role": None}, "member-joined"))
    assert "no longer exists" in missing


def test_remove_role_human():
    text = _run(RemoveRoleDo.human({"do_role": SimpleNamespace(name="muted")}, "contains-text"))
    assert "muted" in text


def test_send_text_human_truncates():
    long_text = "x" * 50
    text = _run(SendTextDo.human(
        {"do_channel": SimpleNamespace(name="alerts"), "do_text": long_text}, "contains-text"))
    assert "#alerts" in text
    assert "..." in text


def test_add_reaction_human():
    text = _run(AddReactionDo.human({"do_emoji": "😀"}, "contains-text"))
    assert "😀" in text
