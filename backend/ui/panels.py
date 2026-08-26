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
        "Thanks for adding me to your server :D Here's some tips on how to get started.\n"
        "This introduction doesn't cover every command — see the README (linked below) for that.",
    )
    add_divider(container)
    add_section(
        container,
        "What is this bot?",
        "Triggered is an if-this-then-that bot for Discord. Create a trigger for a message, "
        "reaction, voice, role, or timed event, then attach one or more actions.",
    )
    add_divider(container)
    add_section(
        container,
        "I'm a developer — how do I make custom triggers?",
        "If you have an idea, go to the [GitHub](https://github.com/quantumbagel/Triggered) "
        "and submit a pull request. You might see your trigger or do in the main bot!",
    )
    add_divider(container)
    add_section(
        container,
        "I'm not a developer — I just want to use this bot!",
        "Read the [README](https://github.com/quantumbagel/Triggered/blob/main/README.md) "
        "for command usage :D",
    )
    add_divider(container)
    add_section(
        container,
        "I can't use /triggered!",
        "Triggered has a settable permission role. If this role is set, you must have it to "
        "use commands. Otherwise, you must be ranked higher in the role hierarchy than Triggered.",
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
