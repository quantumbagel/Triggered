import asyncio
from types import SimpleNamespace

from actions.triggers.contains_text import ContainsTextTrigger
from actions.triggers.contains_word import ContainsWordTrigger
from actions.triggers.everyone_mentioned import EveryoneMentionedTrigger
from actions.triggers.has_attachment import HasAttachmentTrigger
from actions.triggers.in_channel import InChannelTrigger
from actions.triggers.member_boosted import MemberBoostedTrigger
from actions.triggers.message_deleted import MessageDeletedTrigger
from actions.triggers.message_edited import MessageEditedTrigger
from actions.triggers.nickname_changed import NicknameChangedTrigger
from actions.triggers.role_added import RoleAddedTrigger
from actions.triggers.role_removed import RoleRemovedTrigger
from actions.triggers.scheduled import ScheduledTrigger
from actions.triggers.sent_by import SentByTrigger
from actions.triggers.starts_with import StartsWithTrigger
from actions.triggers.user_mentioned import UserMentionedTrigger


def _run(coro):
    return asyncio.run(coro)


def test_contains_text_is_substring():
    variables = {"trigger_text": "hello"}
    assert _run(ContainsTextTrigger.is_valid(variables, SimpleNamespace(content="say hello there")))
    assert not _run(ContainsTextTrigger.is_valid(variables, SimpleNamespace(content="hi")))


def test_contains_word_matches_whole_word_case_insensitive():
    variables = {"trigger_text": "hello"}
    assert _run(ContainsWordTrigger.is_valid(variables, SimpleNamespace(content="Hello, world!")))
    assert _run(ContainsWordTrigger.is_valid(variables, SimpleNamespace(content="say HELLO")))
    assert not _run(ContainsWordTrigger.is_valid(variables, SimpleNamespace(content="helloworld")))
    assert not _run(ContainsWordTrigger.is_valid(variables, SimpleNamespace(content="")))


def test_user_mentioned_matches_by_id():
    member = SimpleNamespace(id=1, name="bob")
    variables = {"trigger_member": member}
    assert _run(UserMentionedTrigger.is_valid(
        variables, SimpleNamespace(mentions=[SimpleNamespace(id=1)])))
    assert not _run(UserMentionedTrigger.is_valid(
        variables, SimpleNamespace(mentions=[SimpleNamespace(id=2)])))
    assert not _run(UserMentionedTrigger.is_valid(
        {"trigger_member": None}, SimpleNamespace(mentions=[SimpleNamespace(id=1)])))


def test_sent_by_matches_author_id():
    variables = {"trigger_member": SimpleNamespace(id=10)}
    assert _run(SentByTrigger.is_valid(
        variables, SimpleNamespace(author=SimpleNamespace(id=10))))
    assert not _run(SentByTrigger.is_valid(
        variables, SimpleNamespace(author=SimpleNamespace(id=11))))
    assert not _run(SentByTrigger.is_valid(
        {"trigger_member": None}, SimpleNamespace(author=SimpleNamespace(id=10))))


def test_in_channel_matches_channel_id():
    variables = {"trigger_channel": SimpleNamespace(id=20, name="general")}
    assert _run(InChannelTrigger.is_valid(
        variables, SimpleNamespace(channel=SimpleNamespace(id=20))))
    assert not _run(InChannelTrigger.is_valid(
        variables, SimpleNamespace(channel=SimpleNamespace(id=21))))
    assert not _run(InChannelTrigger.is_valid(
        {"trigger_channel": None}, SimpleNamespace(channel=SimpleNamespace(id=20))))


def test_has_attachment():
    assert _run(HasAttachmentTrigger.is_valid({}, SimpleNamespace(attachments=["file.png"])))
    assert not _run(HasAttachmentTrigger.is_valid({}, SimpleNamespace(attachments=[])))


def test_everyone_mentioned():
    assert _run(EveryoneMentionedTrigger.is_valid({}, SimpleNamespace(mention_everyone=True)))
    assert not _run(EveryoneMentionedTrigger.is_valid({}, SimpleNamespace(mention_everyone=False)))


def test_starts_with():
    variables = {"trigger_text": "!cmd"}
    assert _run(StartsWithTrigger.is_valid(variables, SimpleNamespace(content="!cmd help")))
    assert not _run(StartsWithTrigger.is_valid(variables, SimpleNamespace(content="hi !cmd")))
    assert not _run(StartsWithTrigger.is_valid({"trigger_text": ""}, SimpleNamespace(content="!cmd")))


def test_message_edited_optional_channel():
    channel = SimpleNamespace(id=3, name="general")
    msg = SimpleNamespace(channel=SimpleNamespace(id=3))
    assert _run(MessageEditedTrigger.is_valid({}, msg))
    assert _run(MessageEditedTrigger.is_valid({"trigger_channel": channel}, msg))
    assert not _run(MessageEditedTrigger.is_valid(
        {"trigger_channel": SimpleNamespace(id=9, name="other")}, msg))


def test_message_deleted_optional_channel():
    channel = SimpleNamespace(id=4, name="alerts")
    msg = SimpleNamespace(channel=SimpleNamespace(id=4))
    assert _run(MessageDeletedTrigger.is_valid({}, msg))
    assert _run(MessageDeletedTrigger.is_valid({"trigger_channel": channel}, msg))
    assert not _run(MessageDeletedTrigger.is_valid(
        {"trigger_channel": SimpleNamespace(id=8, name="other")}, msg))


def test_role_added_and_removed():
    role = SimpleNamespace(id=1, name="alerts")
    other = SimpleNamespace(id=2, name="muted")
    variables = {"trigger_role": role}
    assert _run(RoleAddedTrigger.is_valid(
        variables, [SimpleNamespace(roles=[]), SimpleNamespace(roles=[role])]))
    assert not _run(RoleAddedTrigger.is_valid(
        variables, [SimpleNamespace(roles=[role]), SimpleNamespace(roles=[role])]))
    assert _run(RoleRemovedTrigger.is_valid(
        variables, [SimpleNamespace(roles=[role, other]), SimpleNamespace(roles=[other])]))
    assert not _run(RoleRemovedTrigger.is_valid(
        variables, [SimpleNamespace(roles=[other]), SimpleNamespace(roles=[other])]))


def test_nickname_changed():
    assert _run(NicknameChangedTrigger.is_valid(
        {}, [SimpleNamespace(nick=None), SimpleNamespace(nick="bob")]))
    assert not _run(NicknameChangedTrigger.is_valid(
        {}, [SimpleNamespace(nick="bob"), SimpleNamespace(nick="bob")]))


def test_member_boosted():
    assert _run(MemberBoostedTrigger.is_valid(
        {}, [SimpleNamespace(premium_since=None), SimpleNamespace(premium_since=1)]))
    assert not _run(MemberBoostedTrigger.is_valid(
        {}, [SimpleNamespace(premium_since=1), SimpleNamespace(premium_since=1)]))


def test_scheduled_always_valid():
    assert _run(ScheduledTrigger.is_valid({"trigger_text": "5m"}, None))
