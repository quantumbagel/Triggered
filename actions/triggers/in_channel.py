import discord

from actions.triggers.trigger import Trigger


class InChannelTrigger(Trigger):
    async def human(variables: dict):
        channel = variables.get("trigger_channel")
        if channel is None:
            return "Message sent in a channel that no longer exists."
        return f"Message sent in #{channel.name}."

    async def is_valid(variables: dict, message: discord.Message):
        channel = variables.get("trigger_channel")
        if channel is None:
            return False
        return message.channel.id == channel.id

    def dropdown_name(self):
        return "In Channel"
