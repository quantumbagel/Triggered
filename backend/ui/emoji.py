from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import discord

log = logging.getLogger("triggered").getChild("ui.emoji")

EMOJI_SUFFIXES = {".png", ".gif", ".jpg", ".jpeg", ".webp"}
_DISCORD_NAME = re.compile(r"^[a-zA-Z0-9_]{2,32}$")

BASE_EMOJIS = frozenset(
    {
        "bullet",
        "configure",
        "creator",
        "error",
        "first",
        "forward",
        "github",
        "last",
        "learn",
        "logo",
        "next",
        "pointing",
        "previous",
        "settings",
        "success",
        "user",
    }
)


@dataclass
class EmojiEntry:
    fallback: str | None = None
    id: int | None = None
    animated: bool = False


@dataclass
class EmojiConfig:
    entries: dict[str, EmojiEntry] = field(default_factory=dict)
    path: Path | None = None


def load_emoji_config(path: Path) -> EmojiConfig:
    if not path.exists():
        return EmojiConfig(path=path)
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh) or {}
    entries = {
        name: EmojiEntry(
            fallback=str(entry["fallback"]) if entry.get("fallback") is not None else None,
            id=int(entry["id"]) if entry.get("id") is not None else None,
            animated=bool(entry.get("animated", False)),
        )
        for name, entry in data.items()
    }
    return EmojiConfig(entries=entries, path=path)


class EmojiResolver:
    def __init__(self, config: EmojiConfig) -> None:
        self._config = config

    @property
    def config(self) -> EmojiConfig:
        return self._config

    def get(self, name: str) -> str:
        if not name:
            return self._unknown("(empty)")
        return self._render(name)

    def _render(self, name: str) -> str:
        entry = self._config.entries.get(name)
        if entry is None:
            log.warning("Unknown emoji: %s", name)
            return self._unknown(name)
        if entry.id is not None:
            prefix = "a" if entry.animated else ""
            return f"<{prefix}:{name}:{entry.id}>"
        return entry.fallback if entry.fallback is not None else self._unknown(name)

    def _unknown(self, name: str) -> str:
        fallback = self._config.entries.get("error")
        return fallback.fallback if (fallback and fallback.fallback) else "❓"

    async def sync(self, bot: discord.Client) -> EmojiConfig:
        emojis = await bot.fetch_application_emojis()
        by_name = {emoji.name: emoji for emoji in emojis}

        seen_names = set()
        for name, entry in self._config.entries.items():
            emoji = by_name.get(name)
            if emoji:
                entry.id = emoji.id
                entry.animated = emoji.animated
            else:
                entry.id = None
            seen_names.add(name)

        for name, emoji in by_name.items():
            if name not in seen_names:
                self._config.entries[name] = EmojiEntry(
                    fallback=None, id=emoji.id, animated=emoji.animated
                )
        return self._config

    async def upload_missing(self, bot: discord.Client, assets_dir: Path) -> int:
        """Upload custom emojis from assets that aren't on the app yet."""
        if not assets_dir.exists():
            return 0
        existing = {emoji.name: emoji for emoji in await bot.fetch_application_emojis()}
        uploaded = 0
        for path in sorted(assets_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() not in EMOJI_SUFFIXES:
                continue
            name = path.stem
            if name not in BASE_EMOJIS:
                log.warning("Skipping %s; not in the Triggered emoji set", path.name)
                continue
            if not _DISCORD_NAME.fullmatch(name):
                log.error("Cannot upload emoji %s as %r", path, name)
                continue
            if name in existing:
                created = existing[name]
            else:
                with path.open("rb") as fh:
                    created = await bot.create_application_emoji(name=name, image=fh.read())
                uploaded += 1
            if name in self._config.entries:
                self._config.entries[name].id = created.id
                self._config.entries[name].animated = created.animated
            else:
                self._config.entries[name] = EmojiEntry(
                    fallback=None, id=created.id, animated=created.animated
                )
        return uploaded
