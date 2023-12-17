import discord
import actions.triggers.Trigger as Trigger


class MemberJoinTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"User joined server!"

    async def is_valid(variables: dict, member: discord.Member):
        return True

    def dropdown_name(self):
        return "Member Joined"
