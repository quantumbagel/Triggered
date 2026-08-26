import discord

from actions.dos.do import Do


class SendTextDo(Do):
    async def human(variables: dict, trigger_id: str):
        channel = variables.get("do_channel")
        text = variables.get("do_text")
        if channel is None:
            return "Sent custom text to a channel that no longer exists."
        if not text:
            return f"Sent custom text to #{channel.name}."
        preview = text if len(text) <= 40 else text[:37] + "..."
        return f"Sent \"{preview}\" to #{channel.name}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        channel = data["do"].get("do_channel")
        text = data["do"].get("do_text")
        if channel is None or not text:
            return
        await channel.send(text)

    def dropdown_name(self):
        return "Send Text"
