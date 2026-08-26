import discord

from actions.triggers.trigger import Trigger


class UserMentionedTrigger(Trigger):
    async def human(variables: dict):
        member = variables.get("trigger_member")
        if member is None:
            return "Message sent mentioning a member who is no longer in this server."
        return f"Message sent mentioning @{member.name}."

    async def is_valid(variables: dict, message: discord.Message):
        member = variables.get("trigger_member")
        if member is None:
            return False
        return any(mentioned.id == member.id for mentioned in message.mentions)

    def dropdown_name(self):
        return "User Mentioned"
