import discord

from actions.dos.do import Do


class AddRoleDo(Do):
    async def human(variables: dict, trigger_id: str):
        role = variables.get("do_role")
        if role is None:
            return "Added a role that no longer exists to the member who triggered this."
        return f"Added role @{role.name} to the member who triggered this."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        role = data["do"].get("do_role")
        if role is None or author is None:
            return
        await author.add_roles(role, reason="Triggered: add-role")

    def dropdown_name(self):
        return "Add Role"
