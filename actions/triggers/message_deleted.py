import discord

from actions.triggers.trigger import Trigger


class MessageDeletedTrigger(Trigger):
    async def human(variables: dict):
        channel = variables.get("trigger_channel")
        if channel is None:
            return "A message was deleted."
        return f"A message was deleted in #{channel.name}."

    async def is_valid(variables: dict, message: discord.Message):
        channel = variables.get("trigger_channel")
        if channel is None:
            return True
        return message.channel.id == channel.id

    def dropdown_name(self):
        return "Message Deleted"
