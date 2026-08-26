import discord

from actions.dos.do import Do


class RemoveRoleDo(Do):
    async def human(variables: dict, trigger_id: str):
        role = variables.get("do_role")
        if role is None:
            return "Removed a role that no longer exists from the member who triggered this."
        return f"Removed role @{role.name} from the member who triggered this."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        role = data["do"].get("do_role")
        if role is None or author is None:
            return
        await author.remove_roles(role, reason="Triggered: remove-role")

    def dropdown_name(self):
        return "Remove Role"
