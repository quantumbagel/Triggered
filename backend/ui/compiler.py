from __future__ import annotations

from collections.abc import Awaitable, Callable

import discord
from discord import ui

from backend.ui.components import (
    ActionRow,
    Button,
    ButtonStyle,
    ChannelSelect,
    Container,
    DescribedSelect,
    LayoutView,
    MediaGallery,
    Section,
    Select,
    Separator,
    TextDisplay,
    TextSize,
    UserSelect,
    small_text,
)
from backend.ui.emoji import EmojiResolver

OnAction = Callable[[discord.Interaction, str, dict | None, list[str] | None], Awaitable[None]]


class LayoutError(Exception):
    pass


_STYLE_MAP = {
    ButtonStyle.PRIMARY: discord.ButtonStyle.primary,
    ButtonStyle.SECONDARY: discord.ButtonStyle.secondary,
    ButtonStyle.SUCCESS: discord.ButtonStyle.success,
    ButtonStyle.DANGER: discord.ButtonStyle.danger,
    ButtonStyle.LINK: discord.ButtonStyle.link,
}


class Compiler:
    def __init__(
        self,
        emoji: EmojiResolver,
        *,
        accent_color: discord.Color | None = None,
    ) -> None:
        self._emoji = emoji
        self._accent_color = accent_color
        self._component_count = 0
        self._text_chars = 0

    @property
    def emoji(self) -> EmojiResolver:
        return self._emoji

    def compile(
        self,
        view: LayoutView,
        *,
        on_action: OnAction | None = None,
        timeout: float | None = None,
    ) -> ui.LayoutView:
        self._component_count = 0
        self._text_chars = 0
        layout = ui.LayoutView(timeout=timeout)
        for child in view.children:
            layout.add_item(self._compile_top(child, on_action=on_action))
        if self._component_count > 40:
            raise LayoutError("Layout exceeds 40 components")
        if self._text_chars > 4000:
            raise LayoutError("Layout exceeds 4000 total text characters")
        return layout

    def _count(self) -> None:
        self._component_count += 1

    def _prefix_text(self, text: TextDisplay) -> str:
        content = text.markdown_content
        if text.size_style == TextSize.HEADER and not content.startswith("#"):
            content = f"### {content}"
        elif text.size_style == TextSize.SUBHEADER and not content.startswith(("#", "-#", "**")):
            content = f"**{content}**"
        if len(content) > 4000:
            raise LayoutError("TextDisplay exceeds 4000 characters")
        self._text_chars += len(content)
        return content

    def _resolve_emoji(self, name: str | None) -> str | discord.PartialEmoji | None:
        if not name:
            return None
        resolved = self._emoji.get(name)
        if resolved.startswith("<:") and resolved.endswith(">"):
            inner = resolved[2:-1]
            ename, _, eid = inner.partition(":")
            return discord.PartialEmoji(name=ename, id=int(eid))
        if resolved.startswith("<a:") and resolved.endswith(">"):
            inner = resolved[3:-1]
            ename, _, eid = inner.partition(":")
            return discord.PartialEmoji(name=ename, id=int(eid), animated=True)
        return resolved

    def _bind(self, on_action: OnAction, source: str, payload: dict | None) -> Callable:
        async def callback(interaction: discord.Interaction) -> None:
            values = interaction.data.get("values") if interaction.data else None
            await on_action(interaction, source, payload, values)

        return callback

    def _compile_button(
        self, button: Button, *, on_action: OnAction | None
    ) -> ui.Button:
        self._count()
        if button.style == ButtonStyle.LINK:
            if not button.url:
                raise LayoutError("LINK button requires url")
            return ui.Button(
                style=discord.ButtonStyle.link,
                label=button.label or None,
                url=button.url,
                emoji=self._resolve_emoji(button.emoji),
                disabled=button.disabled,
            )
        compiled = ui.Button(
            style=_STYLE_MAP[button.style],
            label=button.label or None,
            emoji=self._resolve_emoji(button.emoji),
            disabled=button.disabled or not button.source or on_action is None,
        )
        if button.source and on_action is not None and not button.disabled:
            compiled.callback = self._bind(on_action, button.source, button.payload)
        return compiled

    def _compile_select(self, select: Select, *, on_action: OnAction | None) -> ui.Select:
        self._count()
        options = [
            discord.SelectOption(
                label=choice.label[:100],
                value=choice.value[:100],
                description=(choice.description[:100] if choice.description else None),
                emoji=self._resolve_emoji(choice.emoji),
                default=choice.default,
            )
            for choice in select.choices
        ]
        compiled = ui.Select(
            placeholder=select.placeholder,
            min_values=select.min_values,
            max_values=select.max_values,
            options=options or [discord.SelectOption(label="—", value="_")],
            disabled=select.disabled or on_action is None,
        )
        if on_action is not None and not select.disabled:
            compiled.callback = self._bind(on_action, select.source, select.payload)
        return compiled

    _CHANNEL_TYPE_MAP = {
        "text": discord.ChannelType.text,
        "voice": discord.ChannelType.voice,
        "category": discord.ChannelType.category,
        "news": discord.ChannelType.news,
        "stage": discord.ChannelType.stage_voice,
        "forum": discord.ChannelType.forum,
    }

    def _compile_channel_select(
        self, channel_select: ChannelSelect, *, on_action: OnAction | None
    ) -> ui.ChannelSelect:
        self._count()
        channel_types = [
            self._CHANNEL_TYPE_MAP[t]
            for t in channel_select.channel_types
            if t in self._CHANNEL_TYPE_MAP
        ] or [discord.ChannelType.text]
        default_values = (
            [discord.Object(id=channel_select.default_id)]
            if channel_select.default_id is not None
            else []
        )
        compiled = ui.ChannelSelect(
            placeholder=channel_select.placeholder,
            min_values=channel_select.min_values,
            max_values=channel_select.max_values,
            channel_types=channel_types,
            default_values=default_values,
            disabled=channel_select.disabled or on_action is None,
        )
        if on_action is not None and not channel_select.disabled:
            compiled.callback = self._bind(
                on_action, channel_select.source, channel_select.payload
            )
        return compiled

    def _compile_user_select(
        self, user_select: UserSelect, *, on_action: OnAction | None
    ) -> ui.UserSelect:
        self._count()
        compiled = ui.UserSelect(
            placeholder=user_select.placeholder,
            min_values=user_select.min_values,
            max_values=user_select.max_values,
            disabled=user_select.disabled or on_action is None,
        )
        if on_action is not None and not user_select.disabled:
            compiled.callback = self._bind(on_action, user_select.source, user_select.payload)
        return compiled

    def _compile_described_select(
        self, described: DescribedSelect, *, on_action: OnAction | None
    ) -> list[ui.Item]:
        self._count()
        content = small_text(described.description)
        if described.label:
            content = f"{described.label}\n{content}"
        text = ui.TextDisplay(
            content=self._prefix_text(
                TextDisplay(
                    markdown_content=content,
                    size_style=TextSize.BODY,
                )
            )
        )
        self._count()
        separator = ui.Separator(visible=False)
        row = ActionRow()
        if isinstance(described.select, ChannelSelect):
            row.add_channel_select(described.select)
        elif isinstance(described.select, UserSelect):
            row.add_user_select(described.select)
        else:
            row.add_select(described.select)
        return [text, separator, self._compile_action_row(row, on_action=on_action)]

    def _compile_action_row(self, row: ActionRow, *, on_action: OnAction | None) -> ui.ActionRow:
        buttons = [item for item in row.items if isinstance(item, Button)]
        selects = [item for item in row.items if isinstance(item, Select)]
        channel_selects = [item for item in row.items if isinstance(item, ChannelSelect)]
        user_selects = [item for item in row.items if isinstance(item, UserSelect)]
        interactive = buttons + selects + channel_selects + user_selects
        if len(interactive) != len(row.items):
            raise LayoutError("ActionRow contains unsupported items")
        if len(buttons) > 0 and (len(selects) > 0 or len(channel_selects) > 0 or len(user_selects) > 0):
            raise LayoutError("ActionRow cannot mix buttons and selects")
        if len(buttons) > 5:
            raise LayoutError("ActionRow cannot have more than 5 buttons")
        if len(selects) > 1 or len(channel_selects) > 1 or len(user_selects) > 1:
            raise LayoutError("ActionRow cannot have more than 1 select")
        if sum(bool(x) for x in (selects, channel_selects, user_selects)) > 1:
            raise LayoutError("ActionRow cannot mix select types")
        compiled = ui.ActionRow()
        for item in row.items:
            if isinstance(item, Button):
                compiled.add_item(self._compile_button(item, on_action=on_action))
            elif isinstance(item, ChannelSelect):
                compiled.add_item(self._compile_channel_select(item, on_action=on_action))
            elif isinstance(item, UserSelect):
                compiled.add_item(self._compile_user_select(item, on_action=on_action))
            else:
                compiled.add_item(self._compile_select(item, on_action=on_action))
        return compiled

    def _compile_section(self, section: Section, *, on_action: OnAction | None) -> ui.Section:
        self._count()
        compiled_children = []
        for child in section.children:
            self._count()
            compiled_children.append(ui.TextDisplay(content=self._prefix_text(child)))
        if not section.accessory:
            raise LayoutError("Section requires an accessory")
        compiled_accessory = self._compile_button(section.accessory, on_action=on_action)
        return ui.Section(*compiled_children, accessory=compiled_accessory)

    def _compile_container(self, container: Container, *, on_action: OnAction | None) -> ui.Container:
        compiled = ui.Container(accent_color=self._accent_color)
        for child in container.children:
            if isinstance(child, TextDisplay):
                self._count()
                compiled.add_item(ui.TextDisplay(content=self._prefix_text(child)))
            elif isinstance(child, Separator):
                self._count()
                compiled.add_item(ui.Separator(visible=child.visible))
            elif isinstance(child, MediaGallery):
                self._count()
                gallery = ui.MediaGallery(
                    *[
                        discord.MediaGalleryItem(media=item.media_url, description=item.description)
                        for item in child.items
                    ]
                )
                compiled.add_item(gallery)
            elif isinstance(child, ActionRow):
                compiled.add_item(self._compile_action_row(child, on_action=on_action))
            elif isinstance(child, DescribedSelect):
                for item in self._compile_described_select(child, on_action=on_action):
                    compiled.add_item(item)
            elif isinstance(child, Section):
                compiled.add_item(self._compile_section(child, on_action=on_action))
        return compiled

    def _compile_top(self, node: object, *, on_action: OnAction | None) -> ui.Item:
        if isinstance(node, Container):
            return self._compile_container(node, on_action=on_action)
        if isinstance(node, ActionRow):
            return self._compile_action_row(node, on_action=on_action)
        if isinstance(node, TextDisplay):
            self._count()
            return ui.TextDisplay(content=self._prefix_text(node))
        if isinstance(node, Separator):
            self._count()
            return ui.Separator(visible=node.visible)
        if isinstance(node, MediaGallery):
            self._count()
            return ui.MediaGallery(
                *[
                    discord.MediaGalleryItem(media=item.media_url, description=item.description)
                    for item in node.items
                ]
            )
        if isinstance(node, Section):
            return self._compile_section(node, on_action=on_action)
        raise LayoutError(f"Unsupported node type: {type(node)}")
