import discord

from actions.triggers.trigger import Trigger


class StartsWithTrigger(Trigger):
    async def human(variables: dict):
        return f"Message sent starting with \"{variables['trigger_text']}.\""

    async def is_valid(variables: dict, message: discord.Message):
        text = variables.get("trigger_text")
        if not text:
            return False
        return message.content.startswith(text)

    def dropdown_name(self):
        return "Starts With"
