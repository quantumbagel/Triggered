import json
import logging

import discord
from discord import errors

log = logging.getLogger()


async def encode_object(discord_object):
    """
    Encode discord objects (Role, TextChannel, VoiceChannel, Member)
    :param discord_object: The discord object
    :return: the encoded object
    """

    if type(discord_object).__name__ == "Role":
        return ["role", discord_object.id]
    if type(discord_object).__name__ in ["TextChannel", "VoiceChannel"]:
        return ["channel", discord_object.id]
    if type(discord_object).__name__ == "Member":
        return ["member", discord_object.id]
    return discord_object


async def decode_object(d_list, guild_object: discord.Guild):
    """
    Decode the list into a discord object
    :param d_list: The list to decode
    :param guild_object: The guild
    :return: The discord object that has been decoded
    """
    if type(d_list) is not list:
        return d_list
    att = None
    try:
        if d_list[0] == "role":
            att = guild_object.get_role(d_list[1])
        elif d_list[0] == "channel":
            att = await guild_object.fetch_channel(d_list[1])
        elif d_list[0] == "member":
            att = await guild_object.fetch_member(d_list[1])
    except discord.errors.NotFound:
        return att
    return att
