import discord
import actions.triggers.Trigger as Trigger


class ReactionAddedTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"The reaction \"{variables['trigger_emoji']}\" was added."

    async def is_valid(variables: dict, emoji: discord.PartialEmoji):
        return variables["trigger_emoji"] == str(emoji)

    def dropdown_name(self):
        return "Reaction Added"
