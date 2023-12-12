# Triggered by @quantumbagel
import json
import os
import sys
import time
import discord
from discord import app_commands
import logging
import GetTriggerDo
import MongoInterface
import ValidateArguments
import WatchingCommandsUtil

BOT_SECRET = "MTE4MTMzODEzMzIwNDMwNzk2OA.Gw32DT.B-S6t0fQPD5dNOSlFBYd2TF-nuh2TSQC3Zwj9w"
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")


class Triggered(discord.Client):  # A simple client
    def __init__(self, should_sync):
        super().__init__(intents=discord.Intents.all())  # discord.py bug, declare intent to be a bot
        self.synced = False  # sync flag so we don't sync multiple times or hang the bot on reconnects
        self.sync_to = 927616485378129930
        self.should_sync = should_sync

    async def on_ready(self):  # Just sync commands
        global watching_commands
        await self.wait_until_ready()
        if not self.synced and self.should_sync:  # Handle syncing
            log.info("Update detected, performing sync...")
            tree.copy_global_to(guild=discord.Object(id=self.sync_to))
            await tree.sync(guild=discord.Object(id=self.sync_to))
        if not self.synced:
            watching_commands = await watching_commands  # prepare the commands
        self.synced = True
        log.info("(re)Logged into discord!")


async def stringify(input_value):
    if type(input_value) is discord.Role:
        return "@" + input_value.name
    elif type(input_value) is discord.Member:
        return "@" + input_value.global_name
    elif type(input_value) is list:
        return None
    elif type(input_value) is discord.TextChannel:
        return "#" + input_value.name
    elif type(input_value) is discord.VoiceChannel:
        return "#" + input_value.name
    return input_value


async def id_gen(variables: dict, trigger_id: str):
    identification = ''
    for parameter in TRIGGER_REQUIREMENTS[trigger_id]['params'].keys():
        try:
            if TRIGGER_REQUIREMENTS[trigger_id]['params'][parameter]["required"]:
                the_value = await stringify(variables["trigger_" + parameter])
                if the_value is not None:
                    identification += parameter + ":" + the_value + ","
        except TypeError:
            return None
    return identification[:-1]


TRIGGER_REQUIREMENTS, DO_REQUIREMENTS = GetTriggerDo.get_trigger_do()
if DO_REQUIREMENTS is None:  # Error has occurred, print and exit
    log.error(f"Invalid data ({TRIGGER_REQUIREMENTS})")
    sys.exit(1)
log.info("Loaded trigger/do requirements")
try:
    triggered_tracker = json.load(open('configuration/triggered_tracker.json'))
except json.JSONDecodeError:
    log.error("Failed to load triggered_tracker!")
    triggered_tracker = {}
if triggered_tracker == {}:
    log.info("No data, filling with base")
    triggered_tracker = {"conversion": {}, "triggers": {}}
    triggered_tracker.update({'run': time.time()})
TRIGGER_OPTIONS = []
for defined_trigger in TRIGGER_REQUIREMENTS.keys():
    dropdown_key = TRIGGER_REQUIREMENTS[defined_trigger]['class']().dropdown_name()
    TRIGGER_OPTIONS.append(app_commands.Choice(name=dropdown_key, value=defined_trigger))
DO_OPTIONS = []
for defined_do in DO_REQUIREMENTS.keys():
    dropdown_key = DO_REQUIREMENTS[defined_do]['class']().dropdown_name()
    DO_OPTIONS.append(app_commands.Choice(name=dropdown_key, value=defined_do))
print(os.path.getmtime('configuration/requirements.json'), triggered_tracker['run'])
if os.path.getmtime('configuration/requirements.json') > triggered_tracker['run']:
    sync_update = True
else:
    sync_update = False
print(sync_update)
client = Triggered(sync_update)
triggered_tracker.update({'run': time.time()})
json.dump(triggered_tracker, open('configuration/triggered_tracker.json', 'w'))
watching_commands = WatchingCommandsUtil.get_watching_commands(client)
tree = app_commands.CommandTree(client)  # Build command tree

triggered = app_commands.Group(name="triggered", description="The heart and soul of the game.")  # The /triggered group
# I don't think that description is visible anywhere, but maybe it is lol.


@triggered.command(name="new", description="Create a trigger")
@app_commands.choices(trigger=TRIGGER_OPTIONS)
async def new(ctx: discord.Interaction, name: str, trigger: app_commands.Choice[str], trigger_role: discord.Role = None,
              trigger_member: discord.Member = None, trigger_text_or_word: str = None, trigger_emoji: str = None,
              trigger_vc: discord.VoiceChannel = None):
    variables = {"trigger_role": trigger_role, "trigger_member": trigger_member,
                 "trigger_text_or_word": trigger_text_or_word, "trigger_emoji": trigger_emoji, "trigger_vc": trigger_vc}
    allowed, res = ValidateArguments.is_trigger_valid(variables, trigger.value, TRIGGER_REQUIREMENTS)
    if not allowed:
        log.error(f"Failed to validate TRIGGER action (reason=\"{res}\")")
        await ctx.response.send_message(content=f"Invalid arguments! (reason=\"{res}\")", ephemeral=True)
        return
    generated_id = await id_gen(variables, trigger.value)
    if generated_id is None:
        log.error("ID generation failed! :wah:")
        await ctx.response.send_message(content="ID generation failed! This is an issue with the bot."
                                                "\nPlease report your input to @quantumbagel by posting an issue on"
                                                " [GitHub](https://github.com/quantumbagel/Triggered/issues).",
                                        ephemeral=True)
        return
    f_id = trigger.value + "[" + generated_id + "]"
    if str(ctx.guild.id) in watching_commands.keys():
        watching_commands[str(ctx.guild.id)][f_id] = {"trigger_var": variables, "do_var": []}
        triggered_tracker["conversion"][str(ctx.guild.id)][name] = f_id
    else:
        watching_commands.update({str(ctx.guild.id): {f_id: {"trigger_var": variables, "do_var": []}}})
        triggered_tracker["conversion"].update({str(ctx.guild.id): {name: f_id}})
    await WatchingCommandsUtil.update_watching_commands(watching_commands)
    json.dump(triggered_tracker, open('configuration/triggered_tracker.json', 'w'))
    await ctx.response.send_message(content="Trigger created!", ephemeral=True)


@triggered.command(name="add", description="Add a 'do' to a Trigger")
@app_commands.choices(do=DO_OPTIONS)
async def add(ctx: discord.Interaction, trigger_id: str, do: app_commands.Choice[str], do_member: discord.Member = None,
              do_channel: discord.TextChannel = None):
    variables = {"do_member": do_member, "do_channel": do_channel, "do_action_name": do.value}
    allowed, res = ValidateArguments.is_do_valid(variables, do.value, DO_REQUIREMENTS)
    if not allowed:
        log.error(f"Failed to validate TRIGGER action (reason=\"{res}\")")
        await ctx.response.send_message(
            content=f"Invalid arguments! (reason=\"{res}\")")
        return
    try:
        watching_commands[str(ctx.guild.id)][triggered_tracker["conversion"][str(ctx.guild.id)][trigger_id]][
            'do_var'].append(variables)
    except KeyError:
        log.warning("KeyError (probably invalid id)")
        await ctx.response.send_message(content=f"That trigger ({trigger_id}) doesn't exist!")
        return
    await WatchingCommandsUtil.update_watching_commands(watching_commands)
    await ctx.response.send_message(content="Trigger updated!")


async def update_trigger_times(id: str, uid: int, guild_id: int):
    if str(guild_id) in triggered_tracker["triggers"].keys():
        if id not in triggered_tracker["triggers"][str(guild_id)].keys():
            triggered_tracker["triggers"][str(guild_id)][id] = {str(uid): 1}
        else:
            if str(uid) not in triggered_tracker["triggers"][str(guild_id)][id].keys():
                triggered_tracker["triggers"][str(guild_id)][id].update({str(uid): 1})
            else:
                triggered_tracker["triggers"][str(guild_id)][id][str(uid)] += 1
    else:
        triggered_tracker["triggers"].update({str(guild_id): {id: {str(uid): 1}}})
    json.dump(triggered_tracker, open('configuration/triggered_tracker.json', 'w'))


async def _handle(id_type: str, creator: discord.Member = None, guild: discord.Guild = None, other=None):
    if creator.bot:
        log.debug("Ignoring bot creator.")
        return
    if str(guild.id) not in watching_commands:
        log.debug(f"No commands in this guild. (id={guild.id})")
        return
    for trigger in watching_commands[str(guild.id)].keys():
        trigger_id = trigger.split("[")[0]
        try:
            key = next(key for key, value in triggered_tracker["conversion"][str(guild.id)].items() if value == trigger)
        except StopIteration:
            log.warning("Failed to find data :shrug:")
            return
        except KeyError:
            log.warning("Missing data in triggered_tracker!")
            return
        variables = watching_commands[str(guild.id)][trigger]
        if TRIGGER_REQUIREMENTS[trigger_id]["type"] == id_type:
            try:
                if await TRIGGER_REQUIREMENTS[trigger_id]["class"].is_valid(variables["trigger_var"], other):
                    await update_trigger_times(key, creator.id, guild.id)
                    sorted_dictionary = {}
                    for do_id in variables["do_var"]:
                        if not do_id["do_action_name"] in sorted_dictionary.keys():
                            sorted_dictionary[do_id["do_action_name"]] = [do_id]
                        else:
                            sorted_dictionary[do_id["do_action_name"]].append(do_id)
                    for identification in sorted_dictionary:
                        send_over = {"trigger_var": variables["trigger_var"], "do_var": sorted_dictionary[identification]}
                        await DO_REQUIREMENTS[identification]["class"].execute(send_over,
                                                                               variables,
                                                                               trigger,
                                                                               key,
                                                                               client,
                                                                               guild,
                                                                               creator,
                                                                               other_discord_data=other)
            except KeyError as e:
                log.warning(f"Failed is_valid check!\n{e}")


@client.event
async def on_message(msg: discord.Message):
    await _handle("send_msg", msg.author, msg.guild, msg)


@client.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent):
    await _handle("reaction_add", ctx.member, await client.fetch_guild(ctx.guild_id), ctx.emoji)

@client.event
async def on_raw_reaction_remove(ctx: discord.RawReactionActionEvent):
    await _handle("reaction_remove", ctx.member, await client.fetch_guild(ctx.guild_id), ctx.emoji)


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if before.channel != after.channel and after.channel is not None:
        await _handle("vc_join", member, member.guild, [before, after])
    if before.channel != after.channel and after.channel is None:
        await _handle("vc_leave", member, member.guild, [before, after])



@client.event
async def on_guild_join(guild: discord.Guild):
    log.info("Added to guild \"" + guild.name + f"\"! (id={guild.id})")
    embed = discord.Embed(title="Hi! I'm Triggered!",
                          description="Thanks for adding me to your server :D\nHere's some tips on how to get started.")
    embed.add_field(name="What is this bot?",
                    value="Triggered is a IFTTT bot (if-this-then-that) bot designed for programmable triggers"
                          " of everything from a message sent to an article posted online.")
    embed.add_field(name="I'm a developer - How do I make my custom triggers?",
                    value="If you think you have an idea,"
                          " please go to the [GitHub](https://github.com/quantumbagel/Triggered)"
                          " and submit a pull request with your code."
                          " You might see your trigger/do in the main bot!")
    embed.add_field(name="Bro, I'm not a developer - I just want to use this bot!",
                    value="Please read /triggered help for command usage :D")
    embed.add_field(name="I can't use /triggered!",
                    value='You have to have a higher role than the bot to use its commands - this is to prevent access'
                          ' to triggers being created by non-trusted server members.'
                          ' Please ask your admin to get access to Triggered.')
    embed.add_field(name="A quick note to **ADMINS**:",
                    value="Please set the permissions for the commands **NOW**."
                          " (Server Settings/Integrations/Triggered/Manage Bot) "
                          "/reset should be an admin or mod-only command,"
                          " and you should only allow other commands (/triggered)"
                          " to be used by verified server members. "
                          "Do this unless you want to have a bad time with this bot. You have been warned.")
    embed.add_field(name="Who made you?",
                    value="[@quantumbagel on Github](https://github.com/quantumbagel)")

    embed.set_footer(text="Made with ❤ by @quantumbagel", icon_url="https://avatars.githubusercontent.com/u/58365715")

    await guild.system_channel.send(embed=embed)


# @client.event
# async def on_error(error, *args):
#     print(error)
#     print(*args)

try:
    tree.add_command(triggered, guild=discord.Object(id=client.sync_to))
    client.run(BOT_SECRET)
except Exception as e:
    print("Critical error:", e)
    print("This is likely due to:\n1. Internet issues\n2. Incorrect discord token\n3. Incorrectly set up discord bot")
