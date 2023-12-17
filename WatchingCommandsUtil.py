import json
import logging

import discord
from discord import errors

log = logging.getLogger()


async def update_watching_commands(watching_commands: dict):
    """
    Serialize and sync watching_commands with commands.json
    :param watching_commands: The commands to sync
    :return: None
    """
    n_watching_commands = {}
    for guild in watching_commands:
        temp_guild_commands = {}
        for command in watching_commands[guild].keys():
            t_var = {}
            for trigger in watching_commands[guild][command]['trigger_var'].keys():
                if type(watching_commands[guild][command]['trigger_var'][trigger]) not in [bool, str, int, float,
                                                                                           type(None)]:
                    # Is this an Object - i.e. do we need to encode it
                    d_obj = watching_commands[guild][command]['trigger_var'][trigger]
                    t_var.update({trigger: await encode_object(d_obj)})  # Encode the object
                else:
                    # Just pass it in - it's primitive
                    t_var.update({trigger: watching_commands[guild][command]['trigger_var'][trigger]})

            d_var = []
            for index, do in enumerate(watching_commands[guild][command]['do_var']):
                t_do = {}
                for real_do in do.keys():
                    if type(watching_commands[guild][command]['do_var'][index][real_do]) not in [bool, str, int, float,
                                                                                                 type(None)]:
                        # We have an Object
                        d_obj = watching_commands[guild][command]['do_var'][index][real_do]
                        t_do.update({real_do: await encode_object(d_obj)})  # Encode it
                    else:
                        # Pass it in
                        t_do.update({real_do: watching_commands[guild][command]['do_var'][index][real_do]})
                d_var.append(t_do)
            temp_guild_commands.update({command: {"trigger_var": t_var, "do_var": d_var}})
        n_watching_commands.update({guild: temp_guild_commands})
    json.dump(n_watching_commands, open('configuration/commands.json', 'w'))  # Perform update


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


async def get_watching_commands(client: discord.Client):
    """
    Retrieve, deserialize, and restore the watching_commands from commands.json.
    This function is only called when the program starts
    :param client: The bot client
    :return: The commands
    """
    n_watching_commands = {}
    try:
        watching_commands = json.load(open('configuration/commands.json'))
    except json.decoder.JSONDecodeError as jde:
        log.error("Failed to decode JSON!\n" + str(jde))
        return {}  # Bad decode, no commands for you
    for guild in watching_commands:
        guild_object = client.get_guild(guild)
        if guild_object is None:  # Retrieve the guild using an API call (but only if we have to)
            try:
                guild_object = await client.fetch_guild(guild)
            except errors.Forbidden:  # We don't have access to this guild (removed?)
                continue  # so just skip
            except errors.NotFound:  # no longer exists
                continue  # just skip
        temp_guild_commands = {}
        for command in watching_commands[guild].keys():
            t_var = {}
            # Retrieve and decode all triggers
            try:
                for trigger in watching_commands[guild][command]['trigger_var'].keys():
                    if type(watching_commands[guild][command]['trigger_var'][trigger]) is not list:
                        # if the trigger is not a list, just add it
                        t_var.update({trigger: watching_commands[guild][command]['trigger_var'][trigger]})
                        continue
                    else:
                        # We need to decode this, pass to decode_object()
                        decoded_list = watching_commands[guild][command]['trigger_var'][trigger]
                        t_var.update({trigger: await decode_object(decoded_list, guild_object)})
            except KeyError as e:
                log.warning(f"Failed to decode triggers!\nError: {e}")
                return {}
            d_var = []
            # Retrieve and decode all dos. This is a list because there can be multiple dos for each trigger,
            # but there currently can't be duplicates of dos. This could be an interesting feature to implement tho.
            try:
                for index, do in enumerate(watching_commands[guild][command]['do_var']):
                    t_do = {}  # This is like the t_var loop above now.
                    for real_do in do.keys():
                        if type(watching_commands[guild][command]['do_var'][index][real_do]) is not list:
                            # Just passthrough
                            t_do.update({real_do: watching_commands[guild][command]['do_var'][index][real_do]})
                            continue
                        else:
                            # Decode
                            decoded_list = watching_commands[guild][command]['do_var'][index][real_do]
                            t_do.update({real_do: await decode_object(decoded_list, guild_object)})
                    d_var.append(t_do)
            except KeyError as e:
                log.warning(f"Failed to decode dos!\nError: {e}")
                return {}
            temp_guild_commands.update({command: {"trigger_var": t_var, "do_var": d_var}})  # Format t_var and d_var
        n_watching_commands.update({guild: temp_guild_commands})  # Add command to the parsed commands
    return n_watching_commands
