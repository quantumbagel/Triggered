import discord

from actions.triggers.trigger import Trigger


class MemberJoinTrigger(Trigger):
    async def human(variables: dict):
        return f"User joined server!"

    async def is_valid(variables: dict, member: discord.Member):
        return True

    def dropdown_name(self):
        return "Member Joined"
