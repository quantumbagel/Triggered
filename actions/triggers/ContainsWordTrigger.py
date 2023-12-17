import discord
import actions.triggers.Trigger as Trigger


class ContainsWordTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"Message sent containing the word \"{variables['trigger_text']}.\""

    async def is_valid(variables: dict, message: discord.Message):
        return variables["trigger_text"] in message.content.split(' ')

    def dropdown_name(self):
        return "Contains Word"
