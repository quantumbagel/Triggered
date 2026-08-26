import discord

from actions.dos.do import Do
from backend import get_trigger_do
from backend.ui import runtime
from backend.ui.message import send_view
from backend.ui.panels import build_rule_fired_view


class SendMessageDo(Do):
    async def human(variables: dict, trigger_id: str):
        channel = variables.get("do_channel")
        if channel is None:
            return "Sent message to a channel that no longer exists."
        return f"Sent message to #{channel.name}."

    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None):
        trigger_requirements, do_requirements = get_trigger_do.get_trigger_do()
        event_text = await trigger_requirements[data["trigger"]["trigger_action_name"]]['class'].human(
            data["trigger"])
        actions = ''
        for action in data['dos']:
            actions += (":arrow_right:   " +
                        await do_requirements[action["do_action_name"]]['class']
                        .human(action, data["trigger"]["trigger_action_name"]) + '\n')
        actions = actions[:-1]
        message_line = None
        if type(other_discord_data) is discord.Message:
            message_line = f"[{other_discord_data.content}]({other_discord_data.jump_url})"
        avatar_url = None
        if getattr(author, "display_avatar", None) is not None:
            avatar_url = str(author.display_avatar.url)
        view = build_rule_fired_view(
            emoji=runtime.emoji,
            author_name=author.global_name or author.name,
            author_handle=author.name,
            guild_name=guild.name,
            event_text=event_text,
            times_triggered=data["tracker"].get(str(author.id), 1),
            actions=actions,
            message_line=message_line,
            avatar_url=avatar_url,
        )
        await send_view(data['do']['do_channel'], view)

    def dropdown_name(self):
        return "Send Message"
