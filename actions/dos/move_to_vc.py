import discord

from actions.dos.do import Do


class MoveToVCDo(Do):
    async def human(variables: dict, trigger_id: str):
        channel = variables.get("do_vc")
        if channel is None:
            return "Moved the member who triggered this to a voice channel that no longer exists."
        return f"Moved the member who triggered this to :loud_speaker: {channel.name}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        channel = data["do"].get("do_vc")
        if channel is None or author is None:
            return
        await author.move_to(channel, reason="Triggered: move-to-vc")

    def dropdown_name(self):
        return "Move to VC"
