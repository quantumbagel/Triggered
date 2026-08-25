import re

import discord

from actions.triggers.trigger import Trigger


class ContainsWordTrigger(Trigger):
    async def human(variables: dict):
        return f"Message sent containing the word \"{variables['trigger_text']}.\""

    async def is_valid(variables: dict, message: discord.Message):
        text = variables.get("trigger_text")
        if not text:
            return False
        return re.search(r'(?<!\w)' + re.escape(text) + r'(?!\w)', message.content, re.IGNORECASE) is not None

    def dropdown_name(self):
        return "Contains Word"
