import discord
import actions.triggers.Trigger as Trigger


class LeftVCTrigger(Trigger.Trigger):
    async def human(variables: dict):
        return f"Somebody left the VC :loud_sound: {variables['trigger_vc']}."

    async def is_valid(variables: dict, vc_update: list[discord.VoiceState]):
        return vc_update[0].channel == variables['trigger_vc']

    def dropdown_name(self):
        return "Left VC Channel"
