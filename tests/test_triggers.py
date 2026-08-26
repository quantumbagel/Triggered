import asyncio
from types import SimpleNamespace

from actions.triggers.contains_text import ContainsTextTrigger
from actions.triggers.contains_word import ContainsWordTrigger
from actions.triggers.everyone_mentioned import EveryoneMentionedTrigger
from actions.triggers.has_attachment import HasAttachmentTrigger
from actions.triggers.in_channel import InChannelTrigger
from actions.triggers.sent_by import SentByTrigger
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
