import discord

from actions.dos.do import Do


class BanMemberDo(Do):
    async def human(variables: dict, trigger_id: str):
        return "Banned the member who triggered this."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        if author is None or guild is None:
            return
        if author.id in (guild.owner_id, getattr(guild.me, "id", None)):
            return
        await author.ban(reason="Triggered: ban-member", delete_message_seconds=0)

    def dropdown_name(self):
        return "Ban Member"
