import discord

from actions.dos.do import Do


class AddReactionDo(Do):
    async def human(variables: dict, trigger_id: str):
        emoji = variables.get("do_emoji")
        if not emoji:
            return "Added a reaction."
        return f"Added the reaction {emoji}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        emoji = data["do"].get("do_emoji")
        if not emoji or type(other_discord_data) is not discord.Message:
            return
        await other_discord_data.add_reaction(emoji)

    def dropdown_name(self):
        return "Add Reaction"
