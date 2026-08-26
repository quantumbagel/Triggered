import discord

from actions.triggers.trigger import Trigger


class SentByTrigger(Trigger):
    async def human(variables: dict):
        member = variables.get("trigger_member")
        if member is None:
            return "Message sent by a member who is no longer in this server."
        return f"Message sent by @{member.name}."

    async def is_valid(variables: dict, message: discord.Message):
        member = variables.get("trigger_member")
        if member is None:
            return False
        return message.author.id == member.id

    def dropdown_name(self):
        return "Sent By"
