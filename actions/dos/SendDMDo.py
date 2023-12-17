import json
import discord
import actions.dos.Do as Do
import GetTriggerDo


class SendDMDo(Do.Do):
    async def human(variables: dict, trigger_id: str):
        return f"Sent DM to {variables['do_member'].name} (@{variables['do_member'].global_name})."

    async def execute(variables: dict, full_var: dict, trigger_id: str, trigger_name: str, client, guild: discord.Guild,
                      author: discord.Member, other_discord_data=None):
        trigger_requirements, do_requirements = GetTriggerDo.get_trigger_do()
        actual_id = trigger_id.split("[")[0]
        embed = discord.Embed(title=f"Rule triggered by {author.global_name} (@{author.name})",
                              color=discord.Color.from_rgb(255, 87, 51))
        embed.set_thumbnail(url=author.avatar)
        embed.set_author(name=f"Server: {guild.name}",
                         icon_url=guild.icon)
        embed.add_field(name="Event:",
                        value=await trigger_requirements[actual_id]['class'].human(variables["trigger_var"]))
        embed.add_field(name="Triggered:",
                        value=1)
        actions = ''
        for action in full_var['do_var']:
            actions += (":arrow_right:   " +
                        await do_requirements[action["do_action_name"]]['class']
                        .human(action, trigger_id) + '\n')
        actions = actions[:-1]
        embed.add_field(name="Actions taken:",
                        value=actions,
                        inline=False)
        if type(other_discord_data) is discord.Message:
            embed.add_field(name="Message content:",
                            value=f"[{other_discord_data.content}]({other_discord_data.jump_url})")
        embed.set_footer(icon_url="https://avatars.githubusercontent.com/u/58365715",
                         text="Made with ❤ by @quantumbagel")
        for thing in variables['do_var']:
            await thing['do_member'].send(embed=embed)



    def dropdown_name(self):
        return "Send DM"
