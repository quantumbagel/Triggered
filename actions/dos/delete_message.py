import discord

from actions.dos.do import Do


class DeleteMessageDo(Do):
    async def human(variables: dict, trigger_id: str):
        return "Deleted the triggering message."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        if type(other_discord_data) is not discord.Message:
            return
        await other_discord_data.delete()

    def dropdown_name(self):
        return "Delete Message"
