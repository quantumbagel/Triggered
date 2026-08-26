import discord

from actions.triggers.trigger import Trigger


class HasAttachmentTrigger(Trigger):
    async def human(variables: dict):
        return "Message sent with an attachment."

    async def is_valid(variables: dict, message: discord.Message):
        return bool(message.attachments)

    def dropdown_name(self):
        return "Has Attachment"
