from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TextSize(StrEnum):
    HEADER = "header"
    SUBHEADER = "subheader"
    BODY = "body"


class Align(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class ButtonStyle(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    LINK = "link"


@dataclass
class TextDisplay:
    markdown_content: str
    size_style: TextSize = TextSize.BODY
    alignment: Align = Align.LEFT


@dataclass
class Separator:
    visible: bool = True


@dataclass
class MediaGalleryItem:
    media_url: str
    description: str | None = None


@dataclass
class MediaGallery:
    items: list[MediaGalleryItem] = field(default_factory=list)

    def add_item(self, item: MediaGalleryItem) -> MediaGallery:
        self.items.append(item)
        return self


@dataclass
class Section:
    children: list[TextDisplay] = field(default_factory=list)
    accessory: Button | None = None

    def add_text(self, text: TextDisplay) -> Section:
        self.children.append(text)
        return self


@dataclass
class Button:
    source: str = ""
    label: str = ""
    style: ButtonStyle = ButtonStyle.SECONDARY
    emoji: str | None = None
    url: str | None = None
    disabled: bool = False
    payload: dict | None = None


@dataclass
class SelectChoice:
    label: str
    value: str
    description: str | None = None
    emoji: str | None = None
    default: bool = False


@dataclass
class Select:
    source: str
    choices: list[SelectChoice] = field(default_factory=list)
    placeholder: str | None = None
    min_values: int = 1
    max_values: int = 1
    disabled: bool = False
    payload: dict | None = None


@dataclass
class ChannelSelect:
    source: str
    placeholder: str | None = None
    channel_types: tuple[str, ...] = ("text",)
    min_values: int = 1
    max_values: int = 1
    default_id: int | None = None
    disabled: bool = False
    payload: dict | None = None


@dataclass
class UserSelect:
    source: str
    placeholder: str | None = None
    min_values: int = 1
    max_values: int = 1
    disabled: bool = False
    payload: dict | None = None


def small_text(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("-#"):
        return stripped
    return f"-# {stripped}"


@dataclass
class DescribedSelect:
    description: str
    select: Select | ChannelSelect | UserSelect
    label: str | None = None


@dataclass
class ActionRow:
    items: list[Button | Select | ChannelSelect | UserSelect] = field(default_factory=list)

    def add_button(self, button: Button) -> ActionRow:
        self.items.append(button)
        return self

    def add_select(self, select: Select) -> ActionRow:
        self.items.append(select)
        return self

    def add_channel_select(self, channel_select: ChannelSelect) -> ActionRow:
        self.items.append(channel_select)
        return self

    def add_user_select(self, user_select: UserSelect) -> ActionRow:
        self.items.append(user_select)
        return self


@dataclass
class Container:
    children: list[TextDisplay | Separator | MediaGallery | ActionRow | Section | DescribedSelect] = field(
        default_factory=list
    )

    def add_text(self, text: TextDisplay) -> Container:
        self.children.append(text)
        return self

    def add_separator(self, separator: Separator | None = None) -> Container:
        self.children.append(separator if separator is not None else Separator(visible=False))
        return self

    def set_gallery(self, gallery: MediaGallery) -> Container:
        self.children.append(gallery)
        return self

    def add_action_row(self, row: ActionRow) -> Container:
        self.children.append(row)
        return self

    def add_section(self, section: Section) -> Container:
        self.children.append(section)
        return self

    def add_described_select(self, described: DescribedSelect) -> Container:
        self.children.append(described)
        return self


@dataclass
class ViewFile:
    """A file to attach to a layout."""

    data: bytes
    filename: str
    description: str | None = None


@dataclass
class LayoutView:
    children: list[Container | ActionRow | TextDisplay | Separator | MediaGallery | Section] = field(
        default_factory=list
    )
    files: list[ViewFile] = field(default_factory=list)

    def add_container(self, container: Container) -> LayoutView:
        self.children.append(container)
        return self

    @property
    def containers(self) -> list[Container]:
        return [child for child in self.children if isinstance(child, Container)]

    def add_action_row(self, row: ActionRow) -> LayoutView:
        self.children.append(row)
        return self

    def add_section(self, section: Section) -> LayoutView:
        self.children.append(section)
        return self


def walk_interactive(view: LayoutView) -> list[Button | Select | ChannelSelect | UserSelect]:
    items: list[Button | Select | ChannelSelect | UserSelect] = []

    def visit(node: object) -> None:
        if isinstance(node, Button | Select | ChannelSelect | UserSelect):
            items.append(node)
        elif isinstance(node, ActionRow):
            for child in node.items:
                visit(child)
        elif isinstance(node, Container):
            for child in node.children:
                visit(child)
        elif isinstance(node, DescribedSelect):
            visit(node.select)
        elif isinstance(node, Section):
            if node.accessory:
                visit(node.accessory)
            for child in node.children:
                visit(child)
        elif isinstance(node, LayoutView):
            for child in node.children:
                visit(child)

    visit(view)
    return items


def disable_all(view: LayoutView) -> None:
    for item in walk_interactive(view):
        item.disabled = True
