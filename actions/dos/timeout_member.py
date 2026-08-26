from datetime import timedelta

import discord

from actions.dos.do import Do
from backend.duration import parse_duration_seconds


class TimeoutMemberDo(Do):
    async def human(variables: dict, trigger_id: str):
        duration = variables.get("do_text")
        if not duration:
            return "Timed out the member who triggered this."
        return f"Timed out the member who triggered this for {duration}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        if author is None or guild is None:
            return
        if author.id in (guild.owner_id, getattr(guild.me, "id", None)):
            return
        seconds = parse_duration_seconds(data["do"].get("do_text"))
        if not seconds:
            return
        await author.timeout(timedelta(seconds=seconds), reason="Triggered: timeout-member")

    def dropdown_name(self):
        return "Timeout Member"
