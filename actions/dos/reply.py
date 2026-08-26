import discord

from actions.dos.do import Do


class ReplyDo(Do):
    async def human(variables: dict, trigger_id: str):
        text = variables.get("do_text")
        if not text:
            return "Replied to the triggering message."
        preview = text if len(text) <= 40 else text[:37] + "..."
        return f"Replied \"{preview}\" to the triggering message."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        text = data["do"].get("do_text")
        if not text or type(other_discord_data) is not discord.Message:
            return
        await other_discord_data.reply(text)

    def dropdown_name(self):
        return "Reply"
