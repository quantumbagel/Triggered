import json
import discord
import GetTriggerDo
import actions.dos.Do as Do


class SendMessageDo(Do.Do):
    async def human(variables: dict, trigger_id: str):
        return f"Sent message to #{variables['do_channel'].name}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        trigger_requirements, do_requirements = GetTriggerDo.get_trigger_do()
        embed = discord.Embed(title=f"Rule triggered by {author.global_name} (@{author.name})",
                              color=discord.Color.from_rgb(255, 87, 51))
        embed.set_thumbnail(url=author.avatar)
        embed.set_author(name=f"Server: {guild.name}", icon_url=guild.icon)
        embed.add_field(name="Event:",
                        value=await trigger_requirements[data["trigger"]["trigger_action_name"]]['class'].human(
                            data["trigger"]))
        embed.add_field(name="Triggered:",
                        value=1)
        actions = ''
        for action in data['dos']:
            actions += (":arrow_right:   " +
                        await do_requirements[action["do_action_name"]]['class']
                        .human(action, data["trigger"]["trigger_action_name"]) + '\n')
        actions = actions[:-1]
        embed.add_field(name="Actions taken:", value=actions, inline=False)
        if type(other_discord_data) == discord.Message:
            embed.add_field(name="Message content:",
                            value=f"[{other_discord_data.content}]({other_discord_data.jump_url})")
        embed.set_footer(icon_url="https://avatars.githubusercontent.com/u/58365715",
                         text="Made with ❤ by @quantumbagel")
        await data['do']['do_channel'].send(embed=embed)

    def dropdown_name(self):
        return "Send Message"
