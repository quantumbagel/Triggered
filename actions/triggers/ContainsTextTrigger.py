import discord
import actions.triggers.Trigger as Trigger


class ContainsTextTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"Message sent containing the text \"{variables['trigger_text']}.\""

    async def is_valid(variables: dict, message: discord.Message):
        return variables["trigger_text"] in message.content

    def dropdown_name(self):
        return "Contains Text"
