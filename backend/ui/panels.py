from __future__ import annotations

from backend.ui.components import (
    ActionRow,
    Button,
    ButtonStyle,
    Container,
    LayoutView,
    MediaGallery,
    MediaGalleryItem,
)
from backend.ui.emoji import EmojiResolver
from backend.ui.style import add_body, add_divider, add_header, add_section, add_spacer, add_subtitle


def build_trigger_detail_view(
    *,
    emoji: EmojiResolver,
    name: str,
    created_by: str,
    trigger_type: str,
    dos: str,
    activation: str,
    description: str | None,
    last_exec: str,
) -> LayoutView:
    view = LayoutView()
    container = Container()
    add_header(container, f'Trigger "{name}"', emoji=emoji.get("configure"))
    add_subtitle(container, f"Created by {created_by}")
    add_spacer(container)
    add_section(container, "Trigger type", trigger_type)
    add_divider(container)
    add_section(container, "Dos", dos)
    add_divider(container)
    add_section(container, "This trigger was activated", activation)
    add_divider(container)
    add_section(container, "Description", description or "No description provided.")
    add_divider(container)
    add_section(container, "Last execution details", last_exec)
    add_spacer(container)
    add_subtitle(container, "Made with ❤ by @quantumbagel")
    view.add_container(container)
    return view


def build_welcome_view(emoji: EmojiResolver) -> LayoutView:
    view = LayoutView()
    container = Container()
    add_header(container, "Hi! I'm Triggered!", emoji=emoji.get("logo"))
    add_spacer(container)
    add_body(
        container,
        "Thanks for adding me to your server :D\nHere's some tips on how to get started.",
    )
    add_divider(container)
    add_section(
        container,
        "What is this bot?",
        "Triggered is a IFTTT bot (if-this-then-that) for Discord. Message sent, reaction, "
        "voice, role, timer, whatever — then do something.",
    )
    add_divider(container)
    add_section(
        container,
        "I'm a developer - How do I make my custom triggers?",
        "If you think you have an idea, please go to the "
        "[GitHub](https://github.com/quantumbagel/Triggered) and submit a pull request with "
        "your code. You might see your trigger/do in the main bot!",
    )
    add_divider(container)
    add_section(
        container,
        "Bro, I'm not a developer - I just want to use this bot!",
        "Please read the [README](https://github.com/quantumbagel/Triggered/blob/main/README.md) "
        "for command usage :D",
    )
    add_divider(container)
    add_section(
        container,
        "I can't use /triggered!",
        "If a permission role is set, you need it. Otherwise your highest role has to sit "
        "above the bot. Ask an admin if you don't have access.",
    )
    add_divider(container)
    add_section(
        container,
        "A quick note to **ADMINS**:",
        "Set a Required Role in `/triggered server-configure` unless you want random people "
        "making triggers. You have been warned.",
    )
    add_divider(container)
    add_section(
        container,
        "Who made you?",
        "[@quantumbagel on Github](https://github.com/quantumbagel)",
    )

    nav = ActionRow()
    nav.add_button(
        Button(
            label="GitHub Repository",
            style=ButtonStyle.LINK,
            emoji="github",
            url="https://github.com/quantumbagel/Triggered",
        )
    )
    nav.add_button(
        Button(
            label="Readme",
            style=ButtonStyle.LINK,
            emoji="learn",
            url="https://github.com/quantumbagel/Triggered/blob/main/README.md",
        )
    )
    container.add_action_row(nav)
    view.add_container(container)
    return view


def build_rule_fired_view(
    *,
    emoji: EmojiResolver,
    author_name: str,
    author_handle: str,
    guild_name: str,
    event_text: str,
    times_triggered: int,
    actions: str,
    message_line: str | None = None,
    avatar_url: str | None = None,
) -> LayoutView:
    view = LayoutView()
    container = Container()
    add_header(container, f"Rule triggered by {author_name}", emoji=emoji.get("pointing"))
    add_subtitle(container, f"Server: {guild_name} · @{author_handle}")
    if avatar_url:
        gallery = MediaGallery()
        gallery.add_item(MediaGalleryItem(media_url=avatar_url, description=author_name))
        container.set_gallery(gallery)
    add_spacer(container)
    add_section(container, "Event", event_text)
    add_divider(container)
    add_section(container, "Triggered", str(times_triggered))
    add_divider(container)
    add_section(container, "Actions taken", actions)
    if message_line:
        add_divider(container)
        add_section(container, "Message content", message_line)
    add_spacer(container)
    add_subtitle(container, "Made with ❤ by @quantumbagel")
    view.add_container(container)
    return view


def build_list_page_view(
    *,
    emoji: EmojiResolver,
    title: str,
    page: int,
    pages: int,
    items: list[dict[str, str]],
) -> LayoutView:
    view = LayoutView()
    container = Container()
    add_header(container, title, emoji=emoji.get("configure"))
    add_subtitle(container, f"Page {page}/{pages}")
    add_spacer(container)
    if not items:
        add_body(container, "Nothing to show on this page.")
    for idx, item in enumerate(items):
        if idx > 0:
            add_divider(container)
        add_section(
            container,
            item["title"],
            f"{item['subtitle']}\n-# {item['trigger_type']} · Dos {item['dos_subtitle']}",
        )
    if pages > 1:
        nav = ActionRow()
        nav.add_button(
            Button(
                source="first",
                style=ButtonStyle.SECONDARY,
                emoji="first",
                disabled=page <= 1,
            )
        )
        nav.add_button(
            Button(
                source="prev",
                style=ButtonStyle.SECONDARY,
                emoji="previous",
                disabled=page <= 1,
            )
        )
        nav.add_button(
            Button(
                source="next",
                style=ButtonStyle.SECONDARY,
                emoji="next",
                disabled=page >= pages,
            )
        )
        nav.add_button(
            Button(
                source="last",
                style=ButtonStyle.SECONDARY,
                emoji="last",
                disabled=page >= pages,
            )
        )
        container.add_action_row(nav)
    view.add_container(container)
    return view
