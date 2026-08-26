import discord

from actions.triggers.trigger import Trigger


class MessageEditedTrigger(Trigger):
    async def human(variables: dict):
        channel = variables.get("trigger_channel")
        if channel is None:
            return "A message was edited."
        return f"A message was edited in #{channel.name}."

    async def is_valid(variables: dict, message: discord.Message):
        channel = variables.get("trigger_channel")
        if channel is None:
            return True
        return message.channel.id == channel.id

    def dropdown_name(self):
        return "Message Edited"
