import discord

from actions.triggers.trigger import Trigger


class RoleAddedTrigger(Trigger):
    async def human(variables: dict):
        role = variables.get("trigger_role")
        if role is None:
            return "A role that no longer exists was added to a member."
        return f"The role @{role.name} was added to a member."

    async def is_valid(variables: dict, members: list[discord.Member]):
        role = variables.get("trigger_role")
        if role is None or not members or len(members) < 2:
            return False
        before, after = members[0], members[1]
        return role in after.roles and role not in before.roles

    def dropdown_name(self):
        return "Role Added"
