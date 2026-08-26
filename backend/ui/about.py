from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from backend import git_tools
from backend.ui.components import (
    ActionRow,
    Button,
    ButtonStyle,
    Container,
    LayoutView,
    Separator,
    TextDisplay,
    TextSize,
)
from backend.ui.emoji import EmojiResolver

GITHUB_URL = "https://github.com/quantumbagel/Triggered"
README_URL = "https://github.com/quantumbagel/Triggered/blob/main/README.md"


def package_version() -> str:
    try:
        return version("triggered")
    except PackageNotFoundError:
        return "1.0.0"


def build_about_view(emoji: EmojiResolver, active_tab: str = "main") -> LayoutView:
    view = LayoutView()
    brand = emoji.get("logo")
    container = Container()

    if active_tab == "main":
        container.add_text(
            TextDisplay(
                markdown_content=f"### {brand} Triggered",
                size_style=TextSize.HEADER,
            )
        )
        container.add_separator(Separator(visible=False))
        container.add_text(
            TextDisplay(
                markdown_content=(
                    "Triggered is a IFTTT discord bot. You pick a **trigger** (something that "
                    "happens) and attach **dos** (stuff the bot should do). Example: if a "
                    "message contains `hello`, ping `#alerts`."
                )
            )
        )
        container.add_separator()
        container.add_text(
            TextDisplay(
                markdown_content=(
                    f"-# Version {package_version()} · {git_tools.get_git_revision_short_hash()}"
                )
            )
        )
        container.add_text(
            TextDisplay(
                markdown_content=(
                    "-# Made by [@quantumbagel](https://github.com/quantumbagel)"
                )
            )
        )

        nav = ActionRow()
        nav.add_button(
            Button(
                source="background",
                label="Background",
                style=ButtonStyle.SECONDARY,
                emoji="learn",
                payload={"tab": "background"},
            )
        )
        nav.add_button(
            Button(
                source="attributions",
                label="Attributions",
                style=ButtonStyle.SECONDARY,
                emoji="creator",
                payload={"tab": "attributions"},
            )
        )
        nav.add_button(
            Button(
                label="GitHub Repository",
                style=ButtonStyle.LINK,
                emoji="github",
                url=GITHUB_URL,
            )
        )
        container.add_action_row(nav)

    elif active_tab == "background":
        forward = emoji.get("forward")
        container.add_text(
            TextDisplay(
                markdown_content=f"### {brand} Triggered {forward} Background",
                size_style=TextSize.HEADER,
            )
        )
        container.add_separator(Separator(visible=False))
        container.add_text(
            TextDisplay(
                markdown_content=(
                    "Some background on how this project came about:\n"
                    "* I wanted a bot that could do “when X happens, do Y” without paying for "
                    "some automation host or writing a new bot every time.\n"
                    "* So Triggered is that: named triggers, attached dos, slash commands, MongoDB.\n"
                    "* The UI is Components V2, same idea as "
                    "[Strife](https://github.com/quantumbagel/Strife).\n\n"
                    "If you like what I've done here, I'm always looking for new opportunities :D"
                )
            )
        )
        container.add_separator(Separator(visible=False))
        container.add_text(
            TextDisplay(
                markdown_content="-# bagel ❤️ OSS: All my projects are open source"
            )
        )

        nav = ActionRow()
        nav.add_button(
            Button(
                source="back",
                label="Back",
                style=ButtonStyle.SECONDARY,
                emoji="previous",
                payload={"tab": "main"},
            )
        )
        container.add_action_row(nav)

    elif active_tab == "attributions":
        forward = emoji.get("forward")
        container.add_text(
            TextDisplay(
                markdown_content=f"### {brand} Triggered {forward} Attributions",
                size_style=TextSize.HEADER,
            )
        )
        container.add_separator(Separator(visible=False))
        container.add_text(
            TextDisplay(
                markdown_content=(
                    "Libraries this bot uses:\n\n"
                    "* **[discord.py](https://github.com/Rapptz/discord.py)** — Discord API wrapper. (MIT)\n"
                    "* **[PyMongo](https://github.com/mongodb/mongo-python-driver)** — MongoDB driver. (Apache 2.0)\n"
                    "* **[emoji](https://github.com/carpedm20/emoji)** — Emoji for Python. (BSD)"
                )
            )
        )
        container.add_separator(Separator(visible=False))
        container.add_text(
            TextDisplay(
                markdown_content=(
                    "Other credits:\n\n"
                    "* **[icons8](https://icons8.com)** — most of the custom emojis. (Free for personal use)\n"
                    "* **[Strife](https://github.com/quantumbagel/Strife)** — I built the layout stuff there first. (MIT)"
                )
            )
        )

        nav = ActionRow()
        nav.add_button(
            Button(
                source="back",
                label="Back",
                style=ButtonStyle.SECONDARY,
                emoji="previous",
                payload={"tab": "main"},
            )
        )
        nav.add_button(
            Button(
                label="Readme",
                style=ButtonStyle.LINK,
                emoji="learn",
                url=README_URL,
            )
        )
        container.add_action_row(nav)

    view.add_container(container)
    return view
