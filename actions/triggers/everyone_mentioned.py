import discord

from actions.triggers.trigger import Trigger


class EveryoneMentionedTrigger(Trigger):
    async def human(variables: dict):
        return "Message sent mentioning @everyone or @here."

    async def is_valid(variables: dict, message: discord.Message):
        return bool(message.mention_everyone)

    def dropdown_name(self):
        return "Everyone Mentioned"
