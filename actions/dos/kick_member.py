import discord

from actions.dos.do import Do


class KickMemberDo(Do):
    async def human(variables: dict, trigger_id: str):
        return "Kicked the member who triggered this."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        if author is None or guild is None:
            return
        if author.id in (guild.owner_id, getattr(guild.me, "id", None)):
            return
        await author.kick(reason="Triggered: kick-member")

    def dropdown_name(self):
        return "Kick Member"
