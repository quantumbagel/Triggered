import asyncio
from types import SimpleNamespace

from actions.dos.add_reaction import AddReactionDo
from actions.dos.add_role import AddRoleDo
from actions.dos.ban_member import BanMemberDo
from actions.dos.delete_message import DeleteMessageDo
from actions.dos.kick_member import KickMemberDo
from actions.dos.move_to_vc import MoveToVCDo
from actions.dos.remove_role import RemoveRoleDo
from actions.dos.reply import ReplyDo
from actions.dos.send_text import SendTextDo
from actions.dos.timeout_member import TimeoutMemberDo


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


def test_reply_human_truncates():
    text = _run(ReplyDo.human({"do_text": "x" * 50}, "contains-text"))
    assert "..." in text


def test_delete_message_human():
    assert "Deleted" in _run(DeleteMessageDo.human({}, "contains-text"))


def test_move_to_vc_human():
    text = _run(MoveToVCDo.human({"do_vc": SimpleNamespace(name="Lounge")}, "join-vc"))
    assert "Lounge" in text


def test_moderation_dos_human():
    assert "Kicked" in _run(KickMemberDo.human({}, "contains-text"))
    assert "Banned" in _run(BanMemberDo.human({}, "contains-text"))
    text = _run(TimeoutMemberDo.human({"do_text": "10m"}, "contains-text"))
    assert "10m" in text
