from __future__ import annotations

import io

import discord

from backend.ui import runtime
from backend.ui.compiler import OnAction
from backend.ui.components import LayoutView, ViewFile
from backend.ui.style import notice_view


def to_discord_files(files: list[ViewFile] | None) -> list[discord.File]:
    converted: list[discord.File] = []
    for item in files or []:
        if not isinstance(item, ViewFile):
            raise TypeError(
                f"LayoutView.files entries must be ViewFile, got {type(item).__name__}"
            )
        kwargs: dict = {
            "fp": io.BytesIO(item.data),
            "filename": item.filename,
        }
        if item.description:
            kwargs["description"] = item.description
        converted.append(discord.File(**kwargs))
    return converted


def compile_view(
    view: LayoutView,
    *,
    on_action: OnAction | None = None,
    compiler=None,
) -> discord.ui.LayoutView:
    used = compiler if compiler is not None else runtime.compiler
    if used is None:
        raise RuntimeError("UI compiler is not configured")
    return used.compile(view, on_action=on_action)


async def send_view(
    target: discord.Interaction | discord.abc.Messageable,
    view: LayoutView,
    *,
    ephemeral: bool = False,
    on_action: OnAction | None = None,
    compiler=None,
) -> discord.Message | None:
    compiled = compile_view(view, on_action=on_action, compiler=compiler)
    files = to_discord_files(view.files)
    if isinstance(target, discord.Interaction):
        kwargs: dict = {"view": compiled}
        if ephemeral:
            kwargs["ephemeral"] = True
        if files:
            kwargs["files"] = files
        if not target.response.is_done():
            await target.response.send_message(**kwargs)
            return await target.original_response()
        return await target.followup.send(**kwargs)
    kwargs = {"view": compiled}
    if files:
        kwargs["files"] = files
    return await target.send(**kwargs)


async def edit_view(
    interaction: discord.Interaction,
    view: LayoutView,
    *,
    on_action: OnAction | None = None,
    compiler=None,
) -> None:
    compiled = compile_view(view, on_action=on_action, compiler=compiler)
    files = to_discord_files(view.files)
    kwargs: dict = {"view": compiled}
    if files:
        kwargs["attachments"] = files
    if not interaction.response.is_done():
        await interaction.response.edit_message(**kwargs)
        return
    if interaction.message is not None:
        await interaction.message.edit(**kwargs)


async def reply_panel(
    target: discord.Interaction | discord.abc.Messageable,
    title: str,
    body: str | None = None,
    *,
    kind: str = "info",
    sections: list[tuple[str, str]] | None = None,
    ephemeral: bool = True,
) -> discord.Message | None:
    icon = None
    if runtime.emoji is not None:
        if kind == "success":
            icon = runtime.emoji.get("success")
        elif kind == "error":
            icon = runtime.emoji.get("error")
        elif kind == "info":
            icon = runtime.emoji.get("logo")
    view = notice_view(title=title, emoji=icon, body=body, sections=sections)
    return await send_view(target, view, ephemeral=ephemeral)
