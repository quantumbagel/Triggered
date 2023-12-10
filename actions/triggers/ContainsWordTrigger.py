import discord
import actions.triggers.Trigger as Trigger


class ContainsWordTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"Message sent containing the word \"{variables['trigger_text_or_word']}.\""

    async def is_valid(variables: dict, message: discord.Message):
        return variables["trigger_text_or_word"] in message.content.split(' ')

    async def dropdown_name(self):
        return "Contains Word"
