import asyncio

from backend.discord_pickler import decode_object, encode_object


def _run(coro):
    return asyncio.run(coro)


def test_passthrough_non_discord_values():
    assert _run(encode_object("hello")) == "hello"
    assert _run(encode_object(None)) is None
    assert _run(encode_object(12)) == 12


def test_decode_non_list_passthrough():
    assert _run(decode_object("hello", None)) == "hello"
    assert _run(decode_object(None, None)) is None
