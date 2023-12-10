# Triggered by @quantumbagel
import json
import sys
import discord
from discord import app_commands
import logging
import GetTriggerDo
import WatchingCommandsUtil

BOT_SECRET = "secret"


class TriggeredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Prepare logger


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(TriggeredFormatter())

log.addHandler(ch)


class Triggered(discord.Client):  # A simple client
    def __init__(self):
        super().__init__(intents=discord.Intents.all())  # discord.py bug, declare intent to be a bot
        self.synced = False  # sync flag so we don't sync multiple times or hang the bot on reconnects
        self.sync_to = 927616485378129930

    async def on_ready(self):  # Just sync commands
        global watching_commands
        await self.wait_until_ready()
        if not self.synced:  # Handle syncing
            # if input("Should I sync command tree?").lower() == 'y':
            #     tree.copy_global_to(guild=discord.Object(id=self.sync_to))
            #     fmt = await tree.sync(guild=discord.Object(id=self.sync_to))
            # else:
            #     fmt = 'nothing'
            fmt = 'lol'
            self.synced = True
            watching_commands = await watching_commands  # prepare the commands
            log.info("Commands synced: " + str(fmt))
        log.info("Logged into discord!")


TRIGGER_OPTIONS = [
    app_commands.Choice(name="Contains Text", value="contains-text"),
    app_commands.Choice(name="Contains Word", value="contains-word"),
    app_commands.Choice(name="Role Mentioned", value="role-mentioned"),
]
DO_OPTIONS = [
    app_commands.Choice(name="Send DM", value="send-dm"),
    app_commands.Choice(name="Send Message", value="send-message"),
]


async def stringify(input_value):
    if type(input_value) is discord.Role:
        return "@" + input_value.name
    elif type(input_value) is discord.Member:
        return "@" + input_value.global_name
    elif type(input_value) is list:
        return None
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
if DO_REQUIREMENTS is None:
    log.error(f"Invalid data ({TRIGGER_REQUIREMENTS})")
    sys.exit(1)
log.info("Loaded trigger/do requirements")
client = Triggered()
watching_commands = WatchingCommandsUtil.get_watching_commands(client)
tree = app_commands.CommandTree(client)  # Build command tree
triggered_tracker = json.load(open('configuration/triggered_tracker.json'))

if triggered_tracker == {}:
    log.info("No data, filling with base")
    triggered_tracker = {"conversion": {}, "triggers": {}}

triggered = app_commands.Group(name="triggered", description="The heart and soul of the game.")  # The /triggered group
# I don't think that description is visible anywhere, but maybe it is lol.


@triggered.command(name="new", description="Create a trigger")
@app_commands.choices(trigger=TRIGGER_OPTIONS)
async def new(ctx: discord.Interaction, name: str, trigger: app_commands.Choice[str], trigger_role: discord.Role = None,
              trigger_member: discord.Member = None, trigger_text_or_word: str = None):
    variables = {"trigger_role": trigger_role, "trigger_member": trigger_member,
                 "trigger_text_or_word": trigger_text_or_word}
    generated_id = await id_gen(variables, trigger.value)
    if generated_id is None:
        await ctx.response.send_message(content="Required argument missing!")
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
    await ctx.response.send_message(content="Trigger created!")


@triggered.command(name="add", description="Add a 'do' to a Trigger")
@app_commands.choices(do=DO_OPTIONS)
async def add(ctx: discord.Interaction, trigger_id: str, do: app_commands.Choice[str], do_member: discord.Member = None,
              do_channel: discord.TextChannel = None):
    variables = {"do_member": do_member, "do_channel": do_channel, "do_action_name": do.value}
    print(watching_commands)
    watching_commands[str(ctx.guild.id)][triggered_tracker["conversion"][str(ctx.guild.id)][trigger_id]][
        'do_var'].append(variables)
    await WatchingCommandsUtil.update_watching_commands(watching_commands)
    await ctx.response.send_message(content="Trigger updated!")


@app_commands.command(name="reset", description="Reset this server's triggers")
async def reset(ctx: discord.Interaction):
    ctx.response.send_message("Not implemented yet.")


async def update_trigger_times(id: str, uid: int, guild_id: int):
    if str(guild_id) in triggered_tracker["triggers"].keys():
        if id not in triggered_tracker["triggers"][str(guild_id)].keys():
            print("set to one (1)")
            triggered_tracker["triggers"][str(guild_id)][id] = {str(uid): 1}
        else:
            if str(uid) not in triggered_tracker["triggers"][str(guild_id)][id].keys():
                print("set to one (2)")
                triggered_tracker["triggers"][str(guild_id)][id].update({str(uid): 1})
            else:
                print("Incremented")
                triggered_tracker["triggers"][str(guild_id)][id][str(uid)] += 1
    else:
        print("Set to one (3)")
        triggered_tracker["triggers"].update({str(guild_id): {id: {str(uid): 1}}})
    json.dump(triggered_tracker, open('configuration/triggered_tracker.json', 'w'))


@client.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return
    if str(msg.guild.id) not in watching_commands:
        return
    print(watching_commands)
    for trigger in watching_commands[str(msg.guild.id)].keys():
        trigger_id = trigger.split("[")[0]
        print(triggered_tracker, msg.guild.id, trigger)
        key = next(key for key, value in triggered_tracker["conversion"][str(msg.guild.id)].items() if value == trigger)
        variables = watching_commands[str(msg.guild.id)][trigger]
        if TRIGGER_REQUIREMENTS[trigger_id]["type"] == "send_msg":
            if await TRIGGER_REQUIREMENTS[trigger_id]["class"].is_valid(variables["trigger_var"], msg):
                await update_trigger_times(key, msg.author.id, msg.guild.id)
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
                                                                           trigger_id,
                                                                           client,
                                                                           msg.guild,
                                                                           msg.author,
                                                                           other_discord_data=msg)


@client.event
async def on_voice_state_change():
    pass


@client.event
async def on_guild_join(guild: discord.Guild):
    log.info("Added to server " + guild.name + f"! (id={guild.id})")
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
