from pathlib import Path

import discord
from discord import ui

from backend.ui.about import build_about_view
from backend.ui.compiler import Compiler, LayoutError
from backend.ui.components import (
    ActionRow,
    Button,
    ButtonStyle,
    Container,
    LayoutView,
    TextDisplay,
    small_text,
    walk_interactive,
)
from backend.ui.emoji import EmojiConfig, EmojiEntry, EmojiResolver, load_emoji_config
from backend.ui.panels import build_list_page_view, build_trigger_detail_view, build_welcome_view
from backend.ui.style import notice_view


def _resolver() -> EmojiResolver:
    names = [
        "logo", "learn", "creator", "github", "previous", "forward", "error",
        "success", "configure", "first", "last", "next", "pointing", "bullet",
    ]
    return EmojiResolver(EmojiConfig(entries={name: EmojiEntry(fallback="x") for name in names}))


def _compiler() -> Compiler:
    return Compiler(_resolver(), accent_color=discord.Color.from_rgb(255, 87, 51))


def test_small_text_prefixes_once():
    assert small_text("hello") == "-# hello"
    assert small_text("-# already") == "-# already"


def test_load_emoji_config():
    config = load_emoji_config(Path("configuration/emoji.json"))
    assert "success" in config.entries
    assert config.entries["success"].fallback == "✅"
    assert _resolver().get("logo") == "x"
    assert _resolver().get("missing") == "x"


def test_notice_view_compiles():
    view = notice_view(title="Hello", emoji="⚡", body="World", sections=[("A", "B")])
    layout = _compiler().compile(view)
    assert isinstance(layout, ui.LayoutView)
    assert layout.timeout is None
    containers = [child for child in layout.children if isinstance(child, ui.Container)]
    assert len(containers) == 1


def test_about_tabs_have_navigation():
    emoji = _resolver()
    main = build_about_view(emoji, "main")
    buttons = [item for item in walk_interactive(main) if isinstance(item, Button)]
    labels = {button.label for button in buttons}
    assert "Background" in labels
    assert "Attributions" in labels
    assert any(button.style == ButtonStyle.LINK and button.url for button in buttons)

    background = build_about_view(emoji, "background")
    bg_buttons = [item for item in walk_interactive(background) if isinstance(item, Button)]
    assert any(button.payload and button.payload.get("tab") == "main" for button in bg_buttons)

    compiled = _compiler().compile(main, on_action=_noop_action)
    assert any(isinstance(child, ui.Container) for child in compiled.children)


async def _noop_action(interaction, source, payload, values):
    return None


def test_about_compiles_with_callbacks():
    view = build_about_view(_resolver(), "main")
    layout = _compiler().compile(view, on_action=_noop_action)
    buttons = [item for item in layout.walk_children() if isinstance(item, ui.Button)]
    assert buttons
    interactive = [button for button in buttons if button.style != discord.ButtonStyle.link]
    assert interactive
    assert all(callable(button.callback) for button in interactive)


def test_welcome_and_detail_compile():
    emoji = _resolver()
    welcome = build_welcome_view(emoji)
    detail = build_trigger_detail_view(
        emoji=emoji,
        name="hello",
        created_by="@bagel",
        trigger_type="Contains Text",
        dos="Send a message",
        activation="1 time across 1 user.",
        description="demo",
        last_exec="never",
    )
    compiler = _compiler()
    compiler.compile(welcome)
    compiler.compile(detail)


def test_list_page_disables_edges():
    emoji = _resolver()
    first = build_list_page_view(
        emoji=emoji,
        title="Server Triggers",
        page=1,
        pages=3,
        items=[{"title": "1. a", "subtitle": "by x", "trigger_type": "Contains Text", "dos_subtitle": "1/3"}],
    )
    buttons = {button.source: button for button in walk_interactive(first) if isinstance(button, Button)}
    assert buttons["first"].disabled is True
    assert buttons["prev"].disabled is True
    assert buttons["next"].disabled is False
    assert buttons["last"].disabled is False


def test_layout_text_limit():
    view = LayoutView()
    container = Container()
    container.add_text(TextDisplay(markdown_content="x" * 4001))
    view.add_container(container)
    try:
        _compiler().compile(view)
        raise AssertionError("expected LayoutError")
    except LayoutError as exc:
        assert "4000" in str(exc)


def test_action_row_button_limit():
    view = LayoutView()
    container = Container()
    row = ActionRow()
    for i in range(6):
        row.add_button(Button(source=str(i), label=str(i)))
    container.add_action_row(row)
    view.add_container(container)
    try:
        _compiler().compile(view, on_action=_noop_action)
        raise AssertionError("expected LayoutError")
    except LayoutError as exc:
        assert "5 buttons" in str(exc)
