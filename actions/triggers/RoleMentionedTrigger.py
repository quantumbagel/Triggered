import discord
import actions.triggers.Trigger as Trigger


class RoleMentionedTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"Message sent mentioning the role @{variables['trigger_role'].name}."

    async def is_valid(variables: dict, message: discord.Message):
        return variables["trigger_role"] in message.role_mentions

    def dropdown_name(self):
        return "Role Mentioned"
