import discord

from actions.triggers.trigger import Trigger


class NicknameChangedTrigger(Trigger):
    async def human(variables: dict):
        return "A member's nickname changed."

    async def is_valid(variables: dict, members: list[discord.Member]):
        if not members or len(members) < 2:
            return False
        before, after = members[0], members[1]
        return before.nick != after.nick

    def dropdown_name(self):
        return "Nickname Changed"
