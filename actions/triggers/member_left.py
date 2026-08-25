import discord

from actions.triggers.trigger import Trigger


class MemberLeaveTrigger(Trigger):
    async def human(variables: dict):
        return f"User left server :("

    async def is_valid(variables: dict, member: discord.Member):
        return True

    def dropdown_name(self):
        return "Member Left"
