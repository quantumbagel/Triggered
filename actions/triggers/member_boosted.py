import discord

from actions.triggers.trigger import Trigger


class MemberBoostedTrigger(Trigger):
    async def human(variables: dict):
        return "A member boosted the server!"

    async def is_valid(variables: dict, members: list[discord.Member]):
        if not members or len(members) < 2:
            return False
        before, after = members[0], members[1]
        return before.premium_since is None and after.premium_since is not None

    def dropdown_name(self):
        return "Member Boosted"
