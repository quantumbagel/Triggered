# Triggered by @quantumbagel.
import json
import logging
import sys
import time

import discord
import pymongo.errors
from discord import app_commands
from pymongo import MongoClient

from backend import (GetTriggerDo, DiscordPickler, ValidateArguments, ValidateConfiguration, PaginationView,
                     TriggeredFormatter)

logging.getLogger("discord").setLevel(logging.INFO)  # Discord.py logging level - INFO
logging.basicConfig(level=logging.DEBUG)
EMBED_COLOR = discord.Color.from_rgb(255, 87, 51)

# Configure root logger
rlog = logging.getLogger("root")
rlog.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)

ch.setFormatter(TriggeredFormatter.TriggeredFormatter())  # custom formatter
rlog.handlers = [ch]  # Make sure to not double print

log = logging.getLogger("triggered")  # Base logger

configuration = json.load(open('configuration/config.json'))
valid_configuration, reason = ValidateConfiguration.validate_config(configuration)
if not valid_configuration:
    log.critical(f"Configuration file (configuration/config.json) is not valid. (reason=\"{reason}\")")
    sys.exit(1)  # Can't run with invalid configuration file.
log.debug("Successfully loaded configuration file!")
# Bot secret
BOT_SECRET = configuration["bot_secret"]
# The maximum dos per trigger
MAX_DOS = configuration["max_dos_per_trigger"]
# Whether the bot should respond to commands
IS_ACTIVE = True

# Variables for the user-configure and server-configure commands

CONFIGURATION_MODES = [app_commands.Choice(name="Get", value="get"),
                       app_commands.Choice(name="Set/Add", value="update"),
                       app_commands.Choice(name="Remove", value="remove"),
                       app_commands.Choice(name="Switch Whitelist/Blacklist", value="switch")]

SERVER_CONFIGURATION_OPTIONS = [app_commands.Choice(name="Required Role", value='role'),
                                app_commands.Choice(name="Channel Whitelist/Blacklist (text/voice) (Trigger)",
                                                    value='ch_blacklist_trigger'),
                                app_commands.Choice(name="Channel Whitelist/Blacklist (text/voice) (Do)",
                                                    value='ch_blacklist_do'),
                                app_commands.Choice(name="Role Whitelist/Blacklist (Trigger)",
                                                    value='role_blacklist_trigger'),
                                app_commands.Choice(name="Role Whitelist/Blacklist (Do)",
                                                    value='role_blacklist_do')]
USER_CONFIGURATION_OPTIONS = [app_commands.Choice(name="User Whitelist/Blacklist (Trigger)",
                                                  value='user_blacklist_trigger'),
                              app_commands.Choice(name="User Whitelist/Blacklist (Do)",
                                                  value='user_blacklist_do')]
TRIGGER_REQUIREMENTS, DO_REQUIREMENTS = GetTriggerDo.get_trigger_do()

if DO_REQUIREMENTS is None:  # Error has occurred, print and exit
    log.critical(f"Invalid data ({TRIGGER_REQUIREMENTS})")
    sys.exit(1)

# Generate TRIGGER_OPTIONS
TRIGGER_OPTIONS = []
for defined_trigger in TRIGGER_REQUIREMENTS.keys():
    dropdown_key = TRIGGER_REQUIREMENTS[defined_trigger]['class']().dropdown_name()
    TRIGGER_OPTIONS.append(app_commands.Choice(name=dropdown_key, value=defined_trigger))

# Generate DO_OPTIONS
DO_OPTIONS = []
for defined_do in DO_REQUIREMENTS.keys():
    dropdown_key = DO_REQUIREMENTS[defined_do]['class']().dropdown_name()
    DO_OPTIONS.append(app_commands.Choice(name=dropdown_key, value=defined_do))
log.debug("Successfully built Options/Requirements!")
client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)  # Build command tree
db_client = MongoClient(host=configuration["mongodb_uri"], serverSelectionTimeoutMS=5000)
# 5 secs to establish a connection
try:
    db_client.aprivatein.command('ismaster')
except pymongo.errors.ServerSelectionTimeoutError:
    log.critical(f"Failed to connect to MongoDB database (uri=\"{configuration['mongodb_uri']}\")")
    sys.exit(1)
log.debug("Successfully connected to MongoDB!")
watching_commands_access = db_client['commands']
triggered = app_commands.Group(name="triggered", description="The heart and soul of the game.")  # The /triggered group
# I don't think that description is visible anywhere, but maybe it is lol.


log.info("Welcome to Triggered by @quantumbagel!")


def generate_simple_embed(title: str, description: str) -> discord.Embed:
    """
    Generate a simple embed
    :param title: the title
    :param description: the description
    :return: the embed
    """
    embed = discord.Embed(title=title, description=description, color=EMBED_COLOR)
    embed.set_footer(text="Made with ❤ by @quantumbagel", icon_url="https://avatars.githubusercontent.com/u/58365715")
    return embed


def obtain_configuration(id: int, is_user=False):
    """
    Get the config for a guild (server)
    :param id: the ID of the user/guild
    :param is_user: obtain user or guild
    :return:
    """
    if not is_user:
        configuration_db = db_client["server-configuration"][str(id)]
        default_values = {"ch_blacklist": {"mode": "blacklist", "value": []},
                          "role_blacklist": {"mode": "blacklist", "value": []},
                          "role": {"value": None}}
    else:
        configuration_db = db_client["user-configuration"][str(id)]
        default_values = {"user_blacklist": {"mode": "whitelist", "value": []}}
    for value in configuration_db.find():
        edit = default_values[dict(value)["type"]]
        for k in edit:
            edit[k] = dict(value)[k]
    return default_values


async def is_allowed(ctx: discord.Interaction, f_log: logging.Logger) -> bool:
    """
    Returns if an interaction should be allowed.
    This checks for:
    * Bot user
    * DM
    * Role permission / positioning if no role set
    :param ctx: the Interaction to checker
    :param f_log: the logger
    :return: true or false
    """
    if not IS_ACTIVE:
        embed = generate_simple_embed("Bot has been disabled!",
                                      "Triggered has been temporarily disabled by @quantumbagel. This"
                                      " is likely due to a critical bug being discovered.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return False
    if ctx.user.bot:
        f_log.warning("Bot users are not allowed to use commands.")
        return False
    if str(ctx.channel.type) == "private":  # No DMs - yet
        f_log.error("Commands don't work in DMs!")
        embed = generate_simple_embed("Commands don't work in DMs!",
                                      "Triggered requires a server for its commands to work."
                                      " Support for some DM commands may come in the future.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return False
    permissions = list(db_client["server-configuration"][str(ctx.guild.id)].find())
    role_list = next((item for item in permissions if item['type'] == "role"), None)["value"]
    decoded_role = await DiscordPickler.decode_object(role_list, ctx.guild)
    if decoded_role is None:
        if ctx.guild.self_role.position > ctx.user.top_role.position and not ctx.guild.owner_id == ctx.user.id:
            f_log.error("User attempted to access with insufficient permission (old method) >:(")
            embed = generate_simple_embed("Insufficient permission!",
                                          "Because a permission role has not been set for this server"
                                          " (or it is invalid),"
                                          " your highest role must be above mine to use my commands!")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return False
    elif decoded_role not in ctx.user.roles:
        f_log.error("User attempted to access with insufficient permission (new method) >:(")
        embed = generate_simple_embed("Insufficient permission!",
                                      "Because a permission role has been set for this server,"
                                      f" you must have the role {decoded_role.mention}.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return False
    return True


@triggered.command(name="new", description="Create a trigger."
                                           " All optional arguments are dependent"
                                           " on the type of trigger that you choose.")
@app_commands.choices(trigger=TRIGGER_OPTIONS)
async def new(ctx: discord.Interaction, name: str, trigger: app_commands.Choice[str], description: str = None,
              trigger_role: discord.Role = None,
              trigger_member: discord.Member = None, trigger_text: str = None, trigger_emoji: str = None,
              trigger_vc: discord.VoiceChannel = None, trigger_channel: discord.TextChannel = None):
    """
    Create a new trigger. This registers the command in MongoDB
    :param ctx: The discord context
    :param name: The ID of the trigger to be created (required)
    :param trigger: The type of trigger to be created (required)
    :param trigger_role: The role as an argument to the trigger. (argument)
    :param trigger_member: The member as an argument to the trigger. (argument)
    :param trigger_text: The text as an argument to the trigger. (argument)
    :param trigger_emoji: The emoji as an argument to the trigger. (argument)
    :param trigger_vc: The voice channel as an argument to the trigger. (argument)
    :param trigger_channel: the text channel as an argument to the trigger (argument)
    :param description: The description of the purpose of the trigger (argument, recommended)
    :return: None
    """
    f_log = log.getChild("bot.new")

    # Validate
    if not await is_allowed(ctx, f_log):
        return
    max_length = configuration['argument_length_limit']
    if len(name) > max_length:
        f_log.error("Trigger length too long!")
        embed = generate_simple_embed(f"The name of this trigger must be length {max_length} or less.",
                                      f"The current length is {len(name)}.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    if description is not None:
        if len(description) > max_length:
            embed = generate_simple_embed(f"The length of your description must be length {max_length} or less.",
                                          f"The current length is {len(description)}.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
    if trigger_text is not None:
        if len(trigger_text) > max_length:
            embed = generate_simple_embed(f"The length of your text input must be length {max_length} or less.",
                                          f"The current length is {len(trigger_text)}.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
    # Encode variables
    variables = {"trigger_role": trigger_role, "trigger_member": trigger_member,
                 "trigger_text": trigger_text, "trigger_emoji": trigger_emoji, "trigger_vc": trigger_vc,
                 "type": "trigger", "trigger_action_name": trigger.value, "trigger_channel": trigger_channel,
                 "trigger_description": description}

    # Ensure validity
    allowed, res = ValidateArguments.is_trigger_valid(variables, trigger.value, TRIGGER_REQUIREMENTS)
    if not allowed:
        f_log.error(f"Failed to validate TRIGGER action (reason=\"{res}\")")
        embed = generate_simple_embed("Invalid arguments!", f"Reason: \"{res}\"")
        await ctx.response.send_message(embed=embed,
                                        ephemeral=True)
        return

    # Encode variables
    n_var = {}
    for variable in variables.keys():
        n_var[variable] = await DiscordPickler.encode_object(variables[variable])

    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(ctx.guild.id)]
    if str(ctx.guild.id) + "." + name in valid:
        f_log.error("Command already exists! Can't recreate unless deleted.")
        embed = generate_simple_embed(f"That command ({name}) already exists in this server!",
                                      f"If you own this command, please run /triggered delete Trigger {name}.")
        await ctx.response.send_message(embed=embed,
                                        ephemeral=True)
        return

    watching_commands_access[str(ctx.guild.id)][name].insert_one(n_var)
    watching_commands_access[str(ctx.guild.id)][name].insert_one(
        {"type": "meta", "author": await DiscordPickler.encode_object(ctx.user)})
    watching_commands_access[str(ctx.guild.id)][name].insert_one(
        {"type": "tracker"})
    watching_commands_access[str(ctx.guild.id)][name].insert_one(
        {"type": "last_exec", "value": "This trigger has not been activated yet."})
    embed = generate_simple_embed(f"Trigger \"{name}\" created!", "Way to go!")
    await ctx.response.send_message(embed=embed, ephemeral=True)


@triggered.command(name="add", description="Add a do to a Trigger."
                                           " All optional arguments are dependent on the type of do that you choose.")
@app_commands.choices(do=DO_OPTIONS)
async def add(ctx: discord.Interaction, trigger_name: str, do: app_commands.Choice[str], do_name: str,
              description: str = None, do_member: discord.Member = None,
              do_channel: discord.TextChannel = None, do_vc: discord.VoiceChannel = None, do_text: str = None,
              do_role: discord.Role = None, do_emoji: str = None):
    """
    The "add" command. This command adds a do to a selected trigger
    :param do_name: The ID of the do. (required)
    :param do_emoji: The emoji (argument)
    :param do_role: The role (argument)
    :param do_text: The text (argument)
    :param do_vc: The voice channel (argument)
    :param ctx: The discord context
    :param trigger_name: The ID of the existing trigger to add a do to (required).
    :param do: Select the type of do to use. (required)
    :param do_member: The member the do applies to (argument)
    :param do_channel: The channel the do applies to (argument)
    :param description: The description of the purpose of the do (argument, recommended)
    :return: None
    """
    f_log = log.getChild("add")
    # Bot check

    # Validate

    if not await is_allowed(ctx, f_log):
        return

    # Length verification
    max_length = configuration['argument_length_limit']
    if description is not None:
        if len(description) > max_length:
            embed = generate_simple_embed(f"The length of your description must be length {max_length} or less.",
                                          f"The current length is {len(description)}.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
    if do_text is not None:
        if len(do_text) > max_length:
            embed = generate_simple_embed(f"The length of your text input must be length {max_length} or less.",
                                          f"The current length is {len(do_text)}.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

    # Compile the variables
    variables = {"do_member": do_member, "do_channel": do_channel, "do_action_name": do.value,
                 "type": "do", "do_vc": do_vc, "do_text": do_text, "do_role": do_role,
                 "do_emoji": do_emoji, "do_name": do_name, "do_description": description}

    # Ensure that the ID isn't already in use.
    if (watching_commands_access[str(ctx.guild.id)][trigger_name]
            .find_one({"do_name": do_name}, {"_id": False, "type": False}) is not None):
        f_log.error("Do ID already in use by this command!")
        embed = generate_simple_embed(f"The ID ({do_name}) is already in use!",
                                      "Try running this command again, but with a different Do ID"
                                      " (`do_name` parameter)")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    # Get the type of the trigger
    trigger_type = TRIGGER_REQUIREMENTS[dict(watching_commands_access[str(ctx.guild.id)][trigger_name]
                                             .find_one({"type": "trigger"}, {"_id": False, "type": False}))[
        "trigger_action_name"]]["type"]
    # Encode variables
    n_var = {}
    for variable in variables.keys():
        n_var[variable] = await DiscordPickler.encode_object(variables[variable])

    # Validate variables
    allowed, res = ValidateArguments.is_do_valid(variables, do.value, DO_REQUIREMENTS,
                                                 trigger_type)
    if not allowed:  # Not valid, exit now
        f_log.error(f"Failed to validate DO action (reason=\"{res}\")")
        embed = generate_simple_embed("Invalid arguments!",
                                      f"Reason: \"{res}\"")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(ctx.guild.id)]
    if str(ctx.guild.id) + "." + trigger_name in valid:  # Ensure that ID exists
        meta = watching_commands_access[str(ctx.guild.id)][trigger_name].find_one({"type": 'meta'}, {"_id": False,
                                                                                                     "type": False})
        num_dos = len(list(watching_commands_access[str(ctx.guild.id)][trigger_name].find({"type": "do"}, {"_id": False,
                                                                                                           "type": False})))

        author_id = int(meta["author"][1])  # Get the author ID
        if ctx.user.id in [author_id, ctx.guild.owner_id]:  # Allow only the owner and the creator to edit
            if num_dos + 1 > MAX_DOS:
                f_log.warning("Command full of dos!")
                embed = generate_simple_embed(f"That trigger (\"{trigger_name}\")"
                                              f" has used all available {MAX_DOS} dos.",
                                              "Please delete an existing do before adding a new one.")
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return
            watching_commands_access[str(ctx.guild.id)][trigger_name].insert_one(n_var)  # Add to DB
        else:
            f_log.warning("Insufficient permissions!")
            embed = generate_simple_embed("You didn't create this trigger!",
                                          "Therefore, you can't edit it.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
    else:
        f_log.warning("User attempted to access non-existent trigger!")
        embed = generate_simple_embed(f"That trigger ({trigger_name}) doesn't exist!",
                                      "Check your spelling.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    embed = generate_simple_embed(f"Do {do_name} added to trigger {trigger_name}!",
                                  "Make sure to test your trigger to ensure it functions.")
    await ctx.response.send_message(embed=embed, ephemeral=True)


@triggered.command(description="Delete a selected do or trigger. Some arguments are dependent on others.")
@app_commands.choices(to_delete=[app_commands.Choice(name="Trigger", value="trigger"),
                                 app_commands.Choice(name="Do", value="do")])
async def delete(ctx: discord.Interaction, to_delete: app_commands.Choice[str], trigger_name: str, do_name: str = None):
    """
    Delete a do or trigger
    :param ctx:
    :param to_delete: The type of resource to delete (Do/Trigger)
    :param trigger_name: The ID of the trigger to either delete or delete from
    :param do_name: The ID of the do to delete (only required in Do mode)
    :return: None
    """
    f_log = log.getChild("delete")

    # Bot check

    # Validate
    if not await is_allowed(ctx, f_log):
        return

    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(ctx.guild.id)]
    if str(ctx.guild.id) + '.' + trigger_name not in valid:  # Trigger doesn't exist
        f_log.error("Invalid command to delete!")
        embed = generate_simple_embed(f"That command ({trigger_name}) doesn't exist in this server!",
                                      "Check your spelling and try again.")
        await ctx.response.send_message(embed=embed,
                                        ephemeral=True)
        return
    meta = dict(watching_commands_access[str(ctx.guild.id)][trigger_name].find_one({"type": "meta"}, {"_id": False,
                                                                                                      "type": False}))
    if int(meta["author"][1]) != ctx.user.id and ctx.user.id != ctx.guild.owner.id:  # User isn't author of trigger
        f_log.error("User is not author!")
        embed = generate_simple_embed("You didn't create this trigger!",
                                      "Therefore, you can't delete it.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    if to_delete.value == "do" and do_name is None:  # Invalid arguments
        f_log.error("User tried to delete do, but didn't provide ID")
        embed = generate_simple_embed("You have to provide both `trigger_name` and `do_id` to delete a do.",
                                      "Check your spelling and try again.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    elif to_delete.value == 'do':
        value = watching_commands_access[str(ctx.guild.id)][trigger_name].find_one({"do_name": do_name}, {"_id": False,
                                                                                                          "type": False})
        if value is None:  # Invalid arguments
            f_log.error("The trigger ID is valid, but the do ID is invalid")
            embed = generate_simple_embed(f"Your provided `do_name` ({do_name}) was invalid!",
                                          "However, your `trigger_id` was valid.")
            await ctx.response.send_message(
                embed=embed,
                ephemeral=True)
            return

        # Success :D
        watching_commands_access[str(ctx.guild.id)][trigger_name].delete_one({"do_name": do_name})
        embed = generate_simple_embed(f"Successfully deleted do \"{do_name}\" from trigger \"{trigger_name}.\"",
                                      "The trigger does still exist though.")
        await ctx.response.send_message(
            embed=embed,
            ephemeral=True)
    elif to_delete.value == "trigger":
        # Success :D
        watching_commands_access[str(ctx.guild.id)][trigger_name].drop()
        embed = generate_simple_embed(f"Successfully deleted trigger \"{trigger_name}.\"",
                                      "All of its dos have also been deleted.")
        await ctx.response.send_message(
            embed=embed,
            ephemeral=True)


@triggered.command(description="View or search for triggers in this server. Some arguments are dependent on others.")
@app_commands.choices(mode=[app_commands.Choice(name="Search", value="search"),
                            app_commands.Choice(name="View", value="view"),
                            app_commands.Choice(name="List all", value="view-all")])
async def view(ctx: discord.Interaction, mode: app_commands.Choice[str], query: str = None):
    """
    View or search for the server's commands, and use PaginationView to send them.
    :param ctx: The Interaction object
    :param mode: The mode the command should run in
    :param query: The query (if mode is Search or View)
    :return: none
    """
    f_log = log.getChild("view")

    # Validate
    if not await is_allowed(ctx, f_log):
        return

    if mode.value in ["search", "view"] and query is None:  # We need a query for certain modes
        f_log.error(f"Query missing for mode {mode.value}!")
        embed = generate_simple_embed(f"Please provide a query for the mode {mode.name}!",
                                      f"This mode requires an argument (how can you {mode.name.lower()}"
                                      f" something without an argument?)")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(ctx.guild.id)]  # Pool of guild's triggers
    data = []  # Data to send to the PaginationView
    if mode.value in ["search", "view-all"]:
        for index, command in enumerate(valid):  # for every command

            # Just some information about each command, gathered through MongoDB
            cmd_id = command.split('.')[1]
            creator_id = dict(watching_commands_access[command].find_one(
                {"type": "meta"}, {"_id": False, "type": False}))["author"][1]
            num_dos = list(watching_commands_access[command].find({"type": "do"}, {"_id": False,
                                                                                   "type": False}))
            trigger_access = dict(watching_commands_access[command].find_one({"type": "trigger"},
                                                                             {"_id": False, "type": False}))
            dropdown = TRIGGER_REQUIREMENTS[trigger_access['trigger_action_name']]['class']().dropdown_name()

            # Shave an API call
            u = ctx.guild.get_member(creator_id)
            if u is not None:
                creation = f"Created by {u.mention}"
            else:
                u = await client.fetch_user(creator_id)
                creation = f"Created by {u.mention}"

            if mode.value == "search":  # If we are in search mode, we have to check if the query matches
                searchable = [u.global_name.lower(), u.name.lower(), dropdown.lower(), cmd_id.lower()]  # search tokens
                if u.nick is not None:
                    searchable.append(u.nick.lower())  # If we have a nickname, make sure to make it searchable
                valid_response = False  # Don't add it (yet)
                for value in searchable:
                    if query.lower() in value:  # If there's a match
                        valid_response = True  # Add it
                        break
                if valid_response:  # We should add
                    data.append({
                        "title": str(len(data) + 1) + '. ' + cmd_id,
                        "subtitle": creation,
                        "dos_subtitle": f"{len(num_dos)}/{MAX_DOS}",
                        "trigger_type": dropdown
                    })
            elif mode.value == "view-all":  # We're adding everything anyway *shrug*
                data.append({
                    "title": str(len(data) + 1) + '. ' + cmd_id,
                    "subtitle": creation,
                    "dos_subtitle": f"{len(num_dos)}/{MAX_DOS}",
                    "trigger_type": dropdown
                })
        if len(data) != 0:  # There were search results

            # Different title depending on mode
            if mode.value == "view-all":
                title_to_use = "Server Triggers"
            elif mode.value == "search":
                title_to_use = f"Server Results for query \"{query}\""
            else:
                title_to_use = "Title Processing Error"

            pagination_view = (PaginationView.PaginationView
                               (timeout=None, title=title_to_use, data=data, author=ctx.user, embed_color=EMBED_COLOR))
            await pagination_view.send(ctx)
        else:  # There's no search results (or no triggers)
            if mode.value == "search":
                f_log.debug(f"No search results found for query \"{query}!\"")
                embed = generate_simple_embed("No search results found!",
                                              f"It looks like there are no results for your query "
                                              f"\"{query}!\"")
            elif mode.value == "view-all":
                f_log.debug(f"No triggers found in server (name=\"{ctx.guild.name},\" id={ctx.guild.id})!")
                embed = generate_simple_embed("There are no triggers in this server!",
                                              "There are no triggers set up yet in this server."
                                              " Be the first one!")
            else:
                f_log.debug("MA GET THE CAMERA!")
                embed = generate_simple_embed(title="Failed to process input correctly.",
                                              description="Take a screenshot - this should never happen :/")
            await ctx.response.send_message(embed=embed, ephemeral=True)  # Don't bother making a PaginationView
    else:  # We are viewing one command
        if str(ctx.guild.id) + '.' + query not in valid:
            f_log.error(f"Trigger \"{query}\" doesn't exist in server (name=\"{ctx.guild.name},\" id={ctx.guild.id})!")
            error_embed = generate_simple_embed(f"That trigger (\"{query}\") doesn't exist in this server!",
                                                "Check your input.")
            await ctx.response.send_message(embed=error_embed, ephemeral=True)
            return
        creator_id = dict(watching_commands_access[str(ctx.guild.id) + '.' + query]
                          .find_one({"type": "meta"}, {"_id": False, "type": False}))["author"][1]
        trigger_access = dict(watching_commands_access[str(ctx.guild.id) + '.' + query]
                              .find_one({"type": "trigger"}, {"_id": False, "type": False}))
        tracker_access = dict(watching_commands_access[str(ctx.guild.id) + '.' + query]
                              .find_one({"type": "tracker"}, {"_id": False, "type": False}))
        last_exec = dict(watching_commands_access[str(ctx.guild.id) + '.' + query]
                         .find_one({"type": "last_exec"}, {"_id": False, "type": False}))["value"]
        num_triggered = len(tracker_access.keys())
        total_triggered = sum(tracker_access.values())
        pluralizer = ["", ""]  # Good grammar
        if num_triggered != 1:
            pluralizer[1] = "s"
        if total_triggered != 1:
            pluralizer[0] = "s"
        embed = discord.Embed(title=f"Trigger \"{query}\"", color=EMBED_COLOR)
        # Shave an API call
        u = ctx.guild.get_member(creator_id)
        if u is None:
            try:
                u = await client.fetch_user(creator_id)
                mention = u.mention

            except discord.NotFound:
                f_log.error("User not found!")
                mention = "Nonexistent user"
        else:
            mention = u.mention
        actions = ''
        # Get the name of the dropdown (for embed)
        dropdown = TRIGGER_REQUIREMENTS[trigger_access['trigger_action_name']]['class']().dropdown_name()
        for action in list(watching_commands_access[str(ctx.guild.id) + '.' + query]
                                   .find({"type": "do"}, {"_id": False, "type": False})):
            send_action = {}
            for a in action:
                send_action.update({a: await DiscordPickler.decode_object(action[a], ctx.guild)})
            actions += (":arrow_right:   " +
                        await DO_REQUIREMENTS[action["do_action_name"]]['class']
                        .human(send_action, dropdown) + '\n')
        actions = actions[:-1]  # Remove trailing newline
        if actions == '':  # Add a message if no dos are present
            actions = "There are no dos in this trigger!"

        # Create embed with data
        embed.add_field(name="Created by:", value=mention)
        embed.add_field(name="Trigger type:", value=dropdown)
        embed.add_field(name="Dos:", value=actions, inline=False)
        embed.add_field(name="This trigger was activated:",
                        value=f"{total_triggered} time{pluralizer[0]} across {num_triggered} user{pluralizer[1]}.")
        embed.add_field(name="Description:", value=trigger_access['trigger_description'])
        embed.add_field(name="Last execution details:", value=last_exec, inline=False)
        embed.set_footer(text="Made with ❤ by @quantumbagel",
                         icon_url="https://avatars.githubusercontent.com/u/58365715")
        await ctx.response.send_message(embed=embed, ephemeral=True)


async def configurator(ctx: discord.Interaction, configuration_dictionary: dict,
                       variables: dict, human_readable: dict, db_access_loc: str,
                       command_mode: str, conf_option_value: str, conf_option_name: str,
                       default_blacklist_mode="blacklist"):
    if not IS_ACTIVE:  # If the bot isn't online, just quit
        embed = generate_simple_embed("Bot has been disabled!",
                                      "Triggered has been temporarily disabled by @quantumbagel."
                                      " This is likely due to a critical bug being discovered.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    # Get the logger
    f_log = log.getChild(db_access_loc)

    if ctx.user.bot:  # Screw over bots
        f_log.warning("Bot users are not allowed to use commands.")
        return

    if not ctx.user.guild_permissions.administrator:  # If you aren't admin, you can't use this command. Period.
        await ctx.response.send_message(embed=generate_simple_embed("Insufficient permissions!",
                                                                    "You must have the permission"
                                                                    " \"Administrator\" in this server"
                                                                    "to use this command."),
                                        ephemeral=True)
        return

    # Get the value of the current position, or None if it doesn't exist
    current_value_dict = (db_client[db_access_loc][str(ctx.guild.id)]
                          .find_one({"type": conf_option_value},
                                    {"type": False, "_id": False}))

    is_blacklist = configuration_dictionary[conf_option_value]  # Is the selected item a blacklist?
    human_readable_value = human_readable[conf_option_value]  # What's the human_readable name?
    active_variable = variables[conf_option_value]  # What is the value of the *relevant* variable?

    if command_mode == "update" and is_blacklist:  # Case with update, and blacklist mode
        if current_value_dict is not None:  # The value already exists in the DB
            current_value_dict = dict(current_value_dict)
            current_value = current_value_dict["value"]  # The DB value
            mode = current_value_dict["mode"]  # The DB mode
            exists = True  # mark existence
        else:
            # Default value of blacklist parameter
            current_value = []
            mode = default_blacklist_mode
            exists = False  # mark nonexistence
        new_addition = await DiscordPickler.encode_object(active_variable)  # Encode the active variable
        if new_addition in current_value:  # If it's already in the DB, throw an error at the user.
            embed = generate_simple_embed(f"That {human_readable_value}"
                                          f" is already a member "
                                          f"of the {mode}!", "Therefore, you don't need to add it!")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
        current_value.append(new_addition)  # Add to DB list
        if exists:  # If it exists, use .replace_one
            (db_client[db_access_loc][str(ctx.guild.id)]
             .replace_one({"type": conf_option_value},
                          {"value": current_value, "type": conf_option_value, "mode": mode}))
        else:  # If it doesn't, use .insert_one
            db_client[db_access_loc][str(ctx.guild.id)].insert_one({"type": conf_option_value,
                                                                    "value": current_value, "mode": mode})

    elif command_mode == "update" and not is_blacklist:
        # Case with update, but not blacklist mode (single object)
        new_addition = await DiscordPickler.encode_object(active_variable)  # Encode the active variable
        if current_value_dict is not None:  # If it exists, use replace_one
            (db_client[db_access_loc][str(ctx.guild.id)]
             .replace_one({"type": conf_option_value},
                          {"value": new_addition, "type": conf_option_value}))
        else:  # Otherwise, use insert_one
            db_client[db_access_loc][str(ctx.guild.id)].insert_one({"type": conf_option_value,
                                                                    "value": new_addition})

    elif command_mode == "switch" and not is_blacklist:
        # You can't switch a non-blacklist mode!
        embed = generate_simple_embed("You can't switch white/blacklist on a non white/blacklist!",
                                      "Use a list (like Role White/Blacklist)")
        await ctx.response.send_message(embed=embed)

    elif command_mode == "switch" and is_blacklist:
        # You can switch a white/blacklist
        if current_value_dict is not None:
            if current_value_dict["mode"] == "blacklist":
                mode = "whitelist"
            else:
                mode = "blacklist"
            (db_client[db_access_loc][str(ctx.guild.id)]
             .replace_one({"type": conf_option_value},
                          {"type": conf_option_value, "mode": mode,
                           "value": current_value_dict["value"]}))
        else:
            db_client[db_access_loc][str(ctx.guild.id)].insert_one({"type": conf_option_value,
                                                                    "mode": "blacklist", "value": []})

    elif command_mode == "get" and is_blacklist:
        # Get a blacklist
        embed = generate_simple_embed(title=f"Viewing permission \"{conf_option_name}\"", description="")
        all_permissions = ""
        v_permissions = []
        if current_value_dict is not None:
            mode = current_value_dict["mode"]
            for item in current_value_dict["value"]:
                try:
                    decoded = await DiscordPickler.decode_object(item, ctx.guild)
                    v_permissions.append(item)
                    all_permissions += ":arrow_right:   " + decoded.mention + "\n"
                except discord.NotFound:
                    continue
        else:
            mode = "Blacklist"  # Server default is blacklist
        if all_permissions:
            all_permissions = all_permissions[:-1]
        else:
            all_permissions = "None"
        embed.add_field(name="Items in permission:", value=all_permissions)
        embed.add_field(name="Mode:", value=mode.capitalize())
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return  # Don't call response.send_message twice

    elif command_mode == "get" and not is_blacklist:
        # Get a single value
        if current_value_dict is not None:
            current_value_dict = dict(current_value_dict)
            decoded = await DiscordPickler.decode_object(current_value_dict["value"], ctx.guild)
            if decoded is None:
                v = "None"
            else:
                v = decoded.mention
            embed = generate_simple_embed(f"Viewing permission \"{conf_option_name}\"", "")
            embed.add_field(name="Value:", value=v)
        else:
            embed = generate_simple_embed(f"Viewing permission \"{conf_option_name}\"", "")
            embed.add_field(name="Value:", value="None")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    elif command_mode == "remove" and not is_blacklist:
        # Remove a single value
        if current_value_dict is None:
            embed = generate_simple_embed(f"This setting is already not set!",
                                          "Therefore, you can't remove it :(")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            db_client[db_access_loc][str(ctx.guild.id)].delete_one({"type": conf_option_value})
            embed = generate_simple_embed(f"Successfully deleted setting!",
                                          "Thanks for the storage space! :D")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

    elif command_mode == "remove" and is_blacklist:
        if active_variable is None:  # Delete the *entire* list
            if current_value_dict is None:
                embed = generate_simple_embed(f"There is no white/blacklist present here!",
                                              "Therefore, you can't remove it :(")
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                db_client[db_access_loc][str(ctx.guild.id)].delete_one({"type": conf_option_value})
                embed = generate_simple_embed(f"Successfully deleted {current_value_dict['mode']}"
                                              f" \"{conf_option_name}!\"",
                                              "Thanks for the storage space! :D")
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return
        else:
            # Remove a single value from a white/blacklist
            if current_value_dict is None:  # If setting isn't set, you can't use it anyway
                embed = generate_simple_embed(f"This setting is already not set!",
                                              "Therefore, you can't remove it :(")
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return
            else:
                current_value_dict = dict(current_value_dict)
                encoded_object = await DiscordPickler.encode_object(active_variable)
                if encoded_object in current_value_dict["value"]:  # If the item is in the white/blacklist
                    new_value = current_value_dict["value"]  # Obtain the existing list
                    new_value.remove(encoded_object)  # Remove current value
                    # Replace value vvv
                    (db_client[db_access_loc][str(ctx.guild.id)]
                     .replace_one({"type": conf_option_value},
                                  {"type": conf_option_value,
                                   "mode": current_value_dict["mode"],
                                   "value": new_value}))
                    embed = generate_simple_embed(f"Successfully deleted item"
                                                  f" {active_variable.mention}"
                                                  f" from {current_value_dict['mode']}!",
                                                  "Thanks for the storage space! :D")
                    await ctx.response.send_message(embed=embed, ephemeral=True)
                    return
                else:  # We don't have that in the white/blacklist, so we don't need to do
                    embed = generate_simple_embed(f"That {human_readable_value}"
                                                  f" wasn't in the {current_value_dict['mode']} anyway!",
                                                  "Therefore, it wasn't deleted.")
                    await ctx.response.send_message(embed=embed, ephemeral=True)
                    return

    # If we are here, we can say "Updated permissions"
    await ctx.response.send_message(embed=generate_simple_embed("Successfully updated permissions!",
                                                                "Make sure to double-check that the new"
                                                                " configuration is what you want it to be by "
                                                                "using */triggered server-configure Get*."),
                                    ephemeral=True)


@triggered.command(name="server-configure",
                   description="Configure Triggered for this server. Requires the permission \"Administrator.\"")
@app_commands.choices(command_mode=CONFIGURATION_MODES,
                      configuration_option=SERVER_CONFIGURATION_OPTIONS)
async def server_configure(ctx: discord.Interaction, command_mode: app_commands.Choice[str],
                           configuration_option: app_commands.Choice[str], role_obj: discord.Role = None,
                           channel: discord.VoiceChannel | discord.TextChannel = None):
    """
    Set the server permissions - permission "administrator" is required for the user.
    :param command_mode: The mode for the command to function in
    :param configuration_option: Which configuration option to edit/get/update
    :param channel: The channel to add/remove to the white/blacklist
    :param ctx: the discord.Interaction
    :param role_obj: The role to add/remove to the white/blacklist.
    :return: none
    """

    configuration_dictionary = {"role": False,
                                "ch_blacklist": True,
                                "role_blacklist": True}  # Whether each category is a list (True) or not (False)
    # Index each parameter for dynamic access
    variables = {"role": role_obj, "ch_blacklist": channel, "role_blacklist": role_obj}
    # Get the type each parameter is using
    human_readable = {"role": "role", "ch_blacklist": "channel", "role_blacklist": "role"}

    await configurator(ctx, configuration_dictionary, variables, human_readable, "server-configuration",
                       command_mode.value, configuration_option.value, configuration_option.name)


@triggered.command(name="user-configure", description="Configure Triggered for yourself!")
@app_commands.rename(command_mode="mode")
@app_commands.choices(command_mode=CONFIGURATION_MODES,
                      configuration_option=USER_CONFIGURATION_OPTIONS)
async def user_configure(ctx: discord.Interaction, command_mode: app_commands.Choice[str],
                         configuration_option: app_commands.Choice[str], user: discord.Member = None):
    """
    Configures user settings.
    :param ctx: The discord.Interaction
    :param command_mode: The mode for the command to function in
    :param configuration_option: Which configuration option to edit/get/update
    :param user: The user to update/remove
    :return: none
    """

    # Whether each argument is a blacklist/whitelist
    configuration_dictionary = {"user_blacklist_trigger": True, "user_blacklist_do": True}

    # Index each parameter for dynamic access
    variables = {"user_blacklist_trigger": user, "user_blacklist_do": user}
    # Get the type each parameter is using
    human_readable = {"user_blacklist_trigger": "member", "user_blacklist_do": "member"}

    await configurator(ctx, configuration_dictionary, variables, human_readable, "user-configuration",
                       command_mode.value, configuration_option.value, configuration_option.name)


async def handle(id_type: str, creator: discord.Member = None, guild: discord.Guild = None, other=None):
    """
    Handle a generic trigger firing.
    :param id_type: The type of the trigger
    :param creator: The discord.Member responsible for the action
    :param guild: The guild the command is in
    :param other: Other relevant data (passed through to Do.execute())
    :return: None
    """
    f_log = log.getChild(f"event_handler.{id_type}")
    if creator.bot:  # Don't allow bots to activate anything
        f_log.debug("Ignoring bot creator.")
        return
    what_happened = {}
    for database_id in [col for col in list(watching_commands_access.list_collection_names()) if
                        col.split('.')[0] == str(guild.id)]:  # Iterate through each command that this guild has
        start_scan = time.time()
        trigger = database_id.split('.')[1]  # The command name
        what_happened[database_id] = f"Trigger was activated by user \"{creator.global_name}\" (id={creator.id}).\n"
        trigger_dict = dict(watching_commands_access[str(guild.id)][trigger]
                            .find_one({"type": "trigger"}, {'_id': False, "type": False}))  # Trigger data
        submit_trigger_dict = {}
        for item in trigger_dict.keys():
            submit_trigger_dict.update({item: await DiscordPickler.decode_object(trigger_dict[item], guild)})
        if TRIGGER_REQUIREMENTS[submit_trigger_dict["trigger_action_name"]]["type"] == id_type:
            try:
                start_time = time.time()
                try:
                    is_valid = await (TRIGGER_REQUIREMENTS[submit_trigger_dict["trigger_action_name"]]["class"]
                                      .is_valid(submit_trigger_dict, other))
                except Exception as execution_error:
                    what_happened[database_id] += \
                        (f"{TRIGGER_REQUIREMENTS[submit_trigger_dict['trigger_action_name']]['class'].__name__}"
                         f".is_valid call raised an exception: name={type(execution_error)}, value={execution_error}."
                         f" Execution time was {time.time() - start_time} before crash.")
                    continue
                exec_time = time.time() - start_time
                if type(is_valid) is not bool:
                    what_happened[database_id] += (
                        f"{TRIGGER_REQUIREMENTS[submit_trigger_dict['trigger_action_name']]['class'].__name__}"
                        f".is_valid() returned a non-bool type. This type was {type(is_valid)}."
                        f" Arguments passed were submit_trigger_dict={submit_trigger_dict}"
                        f" and other={other}. Execution time was {exec_time}.")
                    continue
                what_happened[database_id] += (f"Successfully checked for is_valid."
                                               f" Execution time was {exec_time}.\n")
                if is_valid:
                    watching_commands_access[database_id].update_one({"type": "tracker"},
                                                                     {"$inc": {str(creator.id): 1}})
                    # The do data from the DB
                    pre_dos = list(watching_commands_access[str(guild.id)][trigger]
                                   .find({"type": "do"}, {'_id': False, 'type': False}))

                    # Decode the "dos" section of the DB
                    submit_dos = []
                    for do in pre_dos:
                        temp_thing = {}
                        for ky in do.keys():
                            temp_thing.update({ky: await DiscordPickler.decode_object(do[ky], guild)})
                        submit_dos.append(temp_thing)

                    # Decode the "meta" section of the DB
                    meta = dict(watching_commands_access[str(guild.id)][trigger]
                                .find_one({"type": "meta"}, {'_id': False, 'type': False}))
                    submit_meta = {}
                    for item in meta.keys():
                        submit_meta.update({item: await DiscordPickler.decode_object(meta[item], guild)})

                    submit_tracker = dict(watching_commands_access[str(guild.id)][trigger]
                                          .find_one({"type": "tracker"}, {'_id': False, 'type': False}))
                    what_happened[database_id] += f"Number of dos to execute: {len(submit_dos)}.\n"
                    for identification in submit_dos:
                        # Compile the data together
                        data = {"do": identification, "dos": submit_dos, "trigger": submit_trigger_dict,
                                "meta": submit_meta,
                                "tracker": submit_tracker}
                        # Perform the execution
                        try:
                            start_time = time.time()
                            await (DO_REQUIREMENTS[identification["do_action_name"]]["class"]
                                   .execute(data, client, guild, creator, other_discord_data=other))
                            exec_time = time.time() - start_time
                            what_happened[database_id] += (
                                f"{DO_REQUIREMENTS[identification['do_action_name']]['class'].__name__}.execute"
                                f" completed successfully."
                                f" Execution time was {exec_time}.\n")
                        except Exception as execution_error:
                            what_happened[database_id] += \
                                (f" {DO_REQUIREMENTS[identification['do_action_name']]['class'].__name__}"
                                 f".execute call raised an exception: name={type(execution_error)}, value={execution_error}."
                                 f" Execution time was {time.time() - start_time} before crash.\n")
                    what_happened[database_id] += (f"Completed trigger \"{trigger}.\""
                                                   f" Total exec time was {time.time() - start_scan}.\n")
                    what_happened[database_id] = what_happened[database_id][:-1]  # Remove trailing newline
                else:
                    what_happened[database_id] = ""
            except KeyError as ke:
                f_log.warning(f"Failed is_valid check!\n{ke}")
        for wh in what_happened:
            if what_happened[wh]:
                result = watching_commands_access[wh].replace_one({"type": "last_exec"},
                                                                  {"value": what_happened[wh], "type": "last_exec"})
                if result.modified_count == 0:
                    watching_commands_access[wh].insert_one({"value": what_happened[wh], "type": "last_exec"})


@client.event
async def on_message(msg: discord.Message):
    """
    Handle the on_message trigger and redirect to handle()
    :param msg: The message
    :return: None
    """
    global IS_ACTIVE
    f_log = log.getChild("event.on_message")
    # Message synchronization command
    if msg.content.startswith("triggered/sync") and msg.author.id == configuration["owner_id"]:  # Perform sync
        split = msg.content.split()
        if len(split) == 1:
            await tree.sync()
        else:
            if split[1] == "this":
                g = msg.guild
            else:
                g = discord.Object(id=int(split[1]))
            tree.copy_global_to(guild=g)
            await tree.sync(guild=g)
        f_log.info("Performed authorized sync.")
        await msg.add_reaction("✅")  # leave confirmation
        return
    elif msg.content == "triggered/disable" and msg.author.id == configuration["owner_id"]:  # Disable bot
        if not IS_ACTIVE:
            await msg.add_reaction("⛔")  # Don't need to disable
            return
        IS_ACTIVE = False
        f_log.critical("BOT HAS BEEN DISABLED!")
        await msg.add_reaction("✅")  # leave confirmation
        return
    elif msg.content == "triggered/enable" and msg.author.id == configuration["owner_id"]:  # Enable bot
        if IS_ACTIVE:
            await msg.add_reaction("⛔")  # Don't need to disable
            return
        IS_ACTIVE = True
        f_log.critical("BOT HAS BEEN ENABLED!")
        await msg.add_reaction("✅")  # leave confirmation
        return
    elif msg.content == "triggered/toggle" and msg.author.id == configuration["owner_id"]:  # Toggle bot
        IS_ACTIVE = not IS_ACTIVE
        if IS_ACTIVE:
            f_log.critical("BOT HAS BEEN ENABLED (TOGGLE)!")
            await msg.add_reaction("✅")  # leave confirmation
        else:
            f_log.critical("BOT HAS BEEN DISABLED (TOGGLE)!")
            await msg.add_reaction("⛔")
        return
    if msg.guild is None:
        return
    f_log.debug(f'Event "on_message" has been triggered! (server="{msg.guild.name}", server_id={msg.guild.id},'
                f' member={msg.author.global_name}, member_id={msg.author.id})')
    await handle("send_msg", msg.author, msg.guild, msg)


@client.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent):
    """
    Handle the reaction_add trigger and redirect to handle()
    :param ctx: The data from discord
    :return: None
    """
    f_log = log.getChild("event.reaction_add")
    event_guild = await client.fetch_guild(ctx.guild_id)
    f_log.debug(f'Event "reaction_add" has been triggered! (server="{event_guild.name}", server_id={event_guild.id},'
                f' member={ctx.member.global_name}, member_id={ctx.member.id})')
    await handle("reaction_add", ctx.member, event_guild, ctx.emoji)


@client.event
async def on_raw_reaction_remove(ctx: discord.RawReactionActionEvent):
    """
    Handle the reaction_remove trigger and redirect to handle()
    :param ctx: The data from discord
    :return: None
    """
    f_log = log.getChild("event.reaction_remove")
    event_guild = await client.fetch_guild(ctx.guild_id)
    identity = ctx.user_id
    u_obj = event_guild.get_member(identity)
    if u_obj is None:
        u_obj = await event_guild.fetch_member(identity)
    f_log.debug(f'Event "reaction_remove" has been triggered! (server="{event_guild.name}", server_id={event_guild.id},'
                f' member={u_obj.global_name}, member_id={u_obj.id})')
    await handle("reaction_remove", u_obj, event_guild, ctx.emoji)


@client.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """
    Handle the vc_join and vc_leave trigger and redirect to handle()
    :param after: the VoiceState after
    :param before: the VoiceState before
    :param member: the member
    :return: None
    """
    f_log = log.getChild("event.voice_state")
    if before.channel != after.channel and after.channel is not None:
        f_log.debug(f'Event "vc_join" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                    f' member={member.global_name}, member_id={member.id})')
        await handle("vc_join", member, member.guild, [before, after])
    if before.channel != after.channel and after.channel is None:
        f_log.debug(f'Event "vc_leave" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                    f' member={member.global_name}, member_id={member.id})')
        await handle("vc_leave", member, member.guild, [before, after])


@client.event
async def on_member_join(member: discord.Member):
    """
    Call handle with the "member_join" event
    :param member: The member who joined
    :return: None
    """
    f_log = log.getChild("event.member_join")
    f_log.debug(f'Event "member_join" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                f' member={member.global_name}, member_id={member.id})')
    await handle("member_join", member, member.guild)


@client.event
async def on_member_remove(member: discord.Member):
    """
    Call handle with the "member_leave" event
    :param member: The member who left :(
    :return: None
    """
    f_log = log.getChild("event.member_leave")
    f_log.info(f"Dropping all triggers from user \"{member.name}\" (id={member.id})")
    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(member.guild.id)]

    dropped = 0
    for command_to_remove in valid:
        if dict(watching_commands_access[command_to_remove]
                        .find_one({"type": "meta"},
                                  {"type": False, "_id": False}))["author"][1] == member.guild.id:
            watching_commands_access.drop_collection(command_to_remove)
            dropped += 1
    f_log.info(f"Dropped {dropped} commands.")
    f_log.debug(f'Event "member_leave" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                f' member={member.global_name}, member_id={member.id})')
    await handle("member_leave", member, member.guild)


@client.event
async def on_guild_join(guild: discord.Guild):
    """
    Send a message to guilds when the bot is added.
    :param guild: the guild the bot was added to
    :return: nothing
    """
    f_log = log.getChild("event.guild_join")
    f_log.info("Added to guild \"" + guild.name + f"\"! (id={guild.id})")
    embed = discord.Embed(title="Hi! I'm Triggered!",
                          description="Thanks for adding me to your server :D\nHere's some tips on how to get started.",
                          color=EMBED_COLOR)
    embed.add_field(name="What is this bot?",
                    value="Triggered is a IFTTT bot (if-this-then-that) bot designed for programmable triggers"
                          " of everything from a message sent to an article posted online.")
    embed.add_field(name="I'm a developer - How do I make my custom triggers?",
                    value="If you think you have an idea,"
                          " please go to the [GitHub](https://github.com/quantumbagel/Triggered)"
                          " and submit a pull request with your code."
                          " You might see your trigger/do in the main bot!")
    embed.add_field(name="Bro, I'm not a developer - I just want to use this bot!",
                    value="Please read the [README](https://github.com/quantumbagel/Triggered/blob/master/README.md)"
                          " for command usage :D")
    embed.add_field(name="I can't use /triggered!",
                    value='You have to have a higher role than the bot to use its commands - this is to prevent access'
                          ' to triggers being created by non-trusted server members.'
                          ' Please ask your aprivatein to get access to Triggered.')
    embed.add_field(name="Who made you?",
                    value="[@quantumbagel on Github](https://github.com/quantumbagel)")

    embed.set_footer(text="Made with ❤ by @quantumbagel", icon_url="https://avatars.githubusercontent.com/u/58365715")

    # Make sure to send in the system channel - if there is none, nothing *should* be sent
    try:
        await guild.system_channel.send(embed=embed)
    except AttributeError:
        f_log.info("No system channel is set - not sending anything.")


@client.event
async def on_guild_remove(guild: discord.Guild):
    """
    Purge data from guilds we were kicked from.
    :param guild: The guild we were removed from
    :return: nothing
    """
    f_log = log.getChild("event.guild_remove")
    f_log.info(f"Dropping all triggers from guild \"{guild.name}\" (id={guild.id})")
    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(guild.id)]
    for command_to_remove in valid:
        watching_commands_access.drop_collection(command_to_remove)
    f_log.info(f"Dropped {len(valid)} commands.")


if __name__ == "__main__":
    try:
        tree.add_command(triggered)
        client.run(BOT_SECRET, log_handler=None)
    except Exception as e:
        log.critical(f"Critical error: {str(e)}")
        log.critical("This is likely due to:\n1. Internet issues\n2. Incorrect discord token\n3. Incorrectly set up "
                     "discord bot")
else:
    log.critical("This file is NOT designed to be imported. Please run bot.py directly!")
