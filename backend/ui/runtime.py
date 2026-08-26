from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.ui.compiler import Compiler
    from backend.ui.emoji import EmojiResolver

compiler: Compiler | None = None
emoji: EmojiResolver | None = None


def configure(next_compiler: Compiler, next_emoji: EmojiResolver) -> None:
    global compiler, emoji
    compiler = next_compiler
    emoji = next_emoji
