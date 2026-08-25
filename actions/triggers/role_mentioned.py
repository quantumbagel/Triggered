import discord

from actions.triggers.trigger import Trigger


class RoleMentionedTrigger(Trigger):
    async def human(variables: dict):
        return f"Message sent mentioning the role @{variables['trigger_role'].name}."

    async def is_valid(variables: dict, message: discord.Message):
        role = variables.get("trigger_role")
        if role is None:
            return False
        return role in message.role_mentions

    def dropdown_name(self):
        return "Role Mentioned"
