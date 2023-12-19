# Triggered by @quantumbagel
import logging
import math
import sys

import discord
from discord import app_commands

import GetTriggerDo
import MongoInterface
import ValidateArguments
import DiscordPickler

BOT_SECRET = open("key").readlines()[0].removesuffix('\n')
MAX_DOS = 3
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")
EMBED_COLOR = discord.Color.from_rgb(255, 87, 51)


class Triggered(discord.Client):  # A simple client
    def __init__(self, should_sync):
        """
        Initialize the client
        :param should_sync: whether a heavily rate limited tree sync should occur (dep)
        """
        super().__init__(intents=discord.Intents.all())  # discord.py bug, declare intent to be a bot
        self.should_sync = should_sync


class PaginationView(discord.ui.View):
    current_page: int = 1
    sep: int = 1

    def __init__(self, timeout=None, title="", data: list[dict[str, str]] = None, author: discord.Member = None):
        """
        Initialize a PaginationView
        :param timeout: the timeout (honestly not sure lol)
        :param title: The title of the View
        """
        super().__init__(timeout=timeout)
        self.title = title
        self.author = author
        self.data = data
        self.message = None

    async def send(self, ctx: discord.Interaction):
        """
        Send the view in a message
        :param ctx: the Interaction
        :return:
        """
        await ctx.response.send_message(view=self)
        self.message = await ctx.original_response()
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        """
        Generate the embed with per-page data
        :param data: the data to parse
        :return: the embed
        """
        embed = discord.Embed(title=f"{self.title} (page {self.current_page}/{math.ceil(len(self.data) / self.sep)})",
                              color=EMBED_COLOR)

        for item in data:
            embed.add_field(name=item['title'], value=item['subtitle'], inline=False)
            embed.add_field(name="Dos", value=item['dos_subtitle'])
            embed.add_field(name="Trigger Name", value=item['trigger_type'])
        embed.set_footer(text="Made with ❤ by @quantumbagel",
                         icon_url="https://avatars.githubusercontent.com/u/58365715")

        return embed

    async def update_message(self, data):
        """
        Update the message (on button click)
        :param data: the data
        :return: none
        """
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def update_buttons(self):
        """
        Update the color and usability of the buttons depending on the current page.
        :return: none
        """
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == math.ceil(len(self.data) / self.sep):
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary

    def get_current_page_data(self):
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        if not self.current_page == 1:
            from_item = 0
            until_item = self.sep
        if self.current_page == math.ceil(len(self.data) / self.sep):
            from_item = self.current_page * self.sep - self.sep
            until_item = len(self.data)
        return self.data[from_item:until_item]

    # These are the buttons and what they do.

    @discord.ui.button(emoji="⏮",
                       style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.defer()
            self.current_page = 1
            await self.update_message(self.get_current_page_data())

    @discord.ui.button(emoji="⬅",
                       style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.defer()
            self.current_page -= 1
            await self.update_message(self.get_current_page_data())

    @discord.ui.button(emoji="➡",
                       style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.defer()
            self.current_page += 1
            await self.update_message(self.get_current_page_data())

    @discord.ui.button(emoji="⏭",
                       style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.author.id:
            await interaction.response.defer()
            self.current_page = math.ceil(len(self.data) / self.sep)
            await self.update_message(self.get_current_page_data())


TRIGGER_REQUIREMENTS, DO_REQUIREMENTS = GetTriggerDo.get_trigger_do()

if DO_REQUIREMENTS is None:  # Error has occurred, print and exit
    log.error(f"Invalid data ({TRIGGER_REQUIREMENTS})")
    sys.exit(1)
log.info("Loaded trigger/do requirements")

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

sync_update = True  # TODO: Add MongoDB dynamic update sync
client = Triggered(sync_update)
tree = app_commands.CommandTree(client)  # Build command tree
db_client = MongoInterface.get_client()
watching_commands_access = db_client['commands']
triggered = app_commands.Group(name="triggered", description="The heart and soul of the game.")  # The /triggered group


# I don't think that description is visible anywhere, but maybe it is lol.

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


@triggered.command(name="new", description="Create a trigger")
@app_commands.choices(trigger=TRIGGER_OPTIONS)
async def new(ctx: discord.Interaction, name: str, trigger: app_commands.Choice[str], description: str = None,
              trigger_role: discord.Role = None,
              trigger_member: discord.Member = None, trigger_text: str = None, trigger_emoji: str = None,
              trigger_vc: discord.VoiceChannel = None, trigger_channel: discord.TextChannel = None):
    """
    Create a new trigger. This registers the command in MongoDB
    :param ctx: The discord context
    :param name: The name of the trigger to be created
    :param trigger: The type of trigger
    :param trigger_role: The role as an argument to the trigger. (optional)
    :param trigger_member: The member as an argument to the trigger. (optional)
    :param trigger_text: The text as an argument to the trigger. (optional)
    :param trigger_emoji: The emoji as an argument to the trigger. (optional)
    :param trigger_vc: The voice channel as an argument to the trigger. (optional)
    :param trigger_channel: the text channel as an argument to the trigger (optional)
    :param description: The description of the purpose of the trigger
    :return: None
    """

    # Bot check
    if ctx.user.bot:
        log.error("User is a bot >>>:(")
        return

    # Ensure permissions
    if ctx.guild.self_role.position > ctx.user.top_role.position and not ctx.guild.owner_id == ctx.user.id:
        log.error("User attempted to access with insufficient permission >:(")
        embed = generate_simple_embed("Insufficient permission!",
                                      "Your highest role must be above mine to use my commands!")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    max_length = 128
    if len(name) > max_length:
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
        log.error(f"Failed to validate TRIGGER action (reason=\"{res}\")")
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
        log.error("Command already exists! Can't recreate unless deleted.")
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
    embed = generate_simple_embed(f"Trigger \"{name}\" created!", "Way to go!")
    await ctx.response.send_message(embed=embed, ephemeral=True)


@triggered.command(name="add", description="Add a 'do' to a Trigger")
@app_commands.choices(do=DO_OPTIONS)
async def add(ctx: discord.Interaction, trigger_name: str, do: app_commands.Choice[str], do_name: str,
              description: str = None, do_member: discord.Member = None,
              do_channel: discord.TextChannel = None, do_vc: discord.VoiceChannel = None, do_text: str = None,
              do_role: discord.Role = None, do_emoji: str = None):
    """
    The "add" command. This command adds a do to a selected trigger
    :param do_name: The name of the "do"
    :param do_emoji: The emoji (argument)
    :param do_role: The role (argument)
    :param do_text: The text (argument)
    :param do_vc: The voice channel (argument)
    :param ctx: The discord context
    :param trigger_name: The name of the trigger to add a do to
    :param do: The do id
    :param do_member: The member the do applies to (optional)
    :param do_channel: The channel the do applies to (optional)
    :param description: The description of the purpose of the do
    :return: None
    """
    # Bot check
    if ctx.user.bot:
        log.error("User is a bot >>>:(")
        return

    # Ensure permissions
    if ctx.guild.self_role.position > ctx.user.top_role.position and not ctx.guild.owner_id == ctx.user.id:
        log.error("User attempted to access with insufficient permission >:(")
        embed = generate_simple_embed("Insufficient permission!",
                                      "Your highest role must be above mine to use my commands!")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    # Length verification
    max_length = 128
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
        log.error("Do ID already in use by this command!")
        embed = generate_simple_embed(f"The ID ({do_name}) is already in use!",
                                      "Try running this command again, but with a different Do ID"
                                      " (`do_name` parameter)")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    # Encode variables
    n_var = {}
    for variable in variables.keys():
        n_var[variable] = await DiscordPickler.encode_object(variables[variable])

    # Validate variables
    allowed, res = ValidateArguments.is_do_valid(variables, do.value, DO_REQUIREMENTS)
    if not allowed:  # Not valid, exit now
        log.error(f"Failed to validate TRIGGER action (reason=\"{res}\")")
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
            if len(num_dos) + 1 > MAX_DOS:
                log.warning("Command full of dos!")
                embed = generate_simple_embed(f"That trigger (\"{trigger_name}\")"
                                              f" has used all available {MAX_DOS} dos.",
                                              "Please delete an existing do before adding a new one.")
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return
            watching_commands_access[str(ctx.guild.id)][trigger_name].insert_one(n_var)  # Add to DB
        else:
            log.warning("Insufficient permissions!")
            embed = generate_simple_embed("You didn't create this trigger!",
                                          "Therefore, you can't edit it.")
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
    else:
        log.warning("User attempted to access non-existent trigger!")
        embed = generate_simple_embed(f"That trigger ({trigger_name}) doesn't exist!",
                                      "Check your spelling.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    embed = generate_simple_embed(f"Do {do_name} added to trigger {trigger_name}!",
                                  "Make sure to test your trigger to ensure it functions.")
    await ctx.response.send_message(embed=embed, ephemeral=True)


@triggered.command(description="Delete a selected do or trigger")
@app_commands.choices(to_delete=[app_commands.Choice(name="Trigger", value="trigger"),
                                 app_commands.Choice(name="Do", value="do")])
async def delete(ctx: discord.Interaction, to_delete: app_commands.Choice[str], trigger_name: str, do_name: str = None):
    # Bot check
    if ctx.user.bot:
        log.error("User is a bot >>>:(")
        return

    if ctx.guild.self_role.position > ctx.user.top_role.position and not ctx.guild.owner_id == ctx.user.id:
        # Insufficient permissions
        log.error("User attempted to access with insufficient permission >:(")
        embed = generate_simple_embed("Insufficient permission!",
                                      "Your highest role must be above mine to use my commands!")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(ctx.guild.id)]
    if str(ctx.guild.id) + '.' + trigger_name not in valid:  # Trigger doesn't exist
        log.error("Invalid command to delete!")
        embed = generate_simple_embed(f"That command ({trigger_name}) doesn't exist in this server!",
                                      "Check your spelling and try again.")
        await ctx.response.send_message(embed=embed,
                                        ephemeral=True)
        return
    meta = dict(watching_commands_access[str(ctx.guild.id)][trigger_name].find_one({"type": "meta"}, {"_id": False,
                                                                                                      "type": False}))
    if int(meta["author"][1]) != ctx.user.id and ctx.user.id != ctx.guild.owner.id:  # User isn't author of trigger
        log.error("User is not author!")
        embed = generate_simple_embed("You didn't create this trigger!",
                                      "Therefore, you can't delete it.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return

    if to_delete.value == "do" and do_name is None:  # Invalid arguments
        log.error("User tried to delete do, but didn't provide ID")
        embed = generate_simple_embed("You have to provide both `trigger_name` and `do_id` to delete a do.",
                                      "Check your spelling and try again.")
        await ctx.response.send_message(embed=embed, ephemeral=True)
        return
    elif to_delete.value == 'do':
        value = watching_commands_access[str(ctx.guild.id)][trigger_name].find_one({"do_name": do_name}, {"_id": False,
                                                                                                          "type": False})
        if value is None:  # Invalid arguments
            log.error("The trigger ID is valid, but the do ID is invalid")
            embed = generate_simple_embed(f"Your provided `do_name` ({do_name}) was invalid!", "However, your `trigger_id` was valid.")
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


@triggered.command(description="View or search for triggers in this server")
@app_commands.choices(mode=[app_commands.Choice(name="Search", value="search"),
                            app_commands.Choice(name="View", value="view"),
                            app_commands.Choice(name="List all", value="view-all")])
async def view(ctx: discord.Interaction, mode: app_commands.Choice[str], query: str = None):
    """
    View or search for the server's commands, and use PaginationView to send them.
    :param ctx: The Interaction object
    :param mode: The mode the command should run in
    :param query: The query (if applicable)
    :return: none
    """
    # Bot check
    if ctx.user.bot:
        log.error("User is a bot >>>:(")
        return
    if mode.value in ["search", "view"] and query is None:  # We need a query for certain modes
        await ctx.response.send_message(f"Please provide a query for the mode {mode.name}!", ephemeral=True)
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
            trigger_access = dict(watching_commands_access[command].find_one({"type": "trigger"}, {"_id": False,
                                                                                                   "type": False}))
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

            pagination_view = PaginationView(timeout=None, title=title_to_use, data=data, author=ctx.user)
            await pagination_view.send(ctx)
        else:  # There's no search results (or no triggers)
            if mode.value == "search":
                embed = generate_simple_embed("No search results found!",
                                              f"It looks like there are no results for your query \"{query}\"")
            elif mode.value == "list-all":
                embed = generate_simple_embed("There are no triggers in this server!",
                                              "There are no triggers set up yet in this server. Be the first one!")
            else:
                embed = generate_simple_embed(title="Failed to process input correctly.",
                                              description="Take a screenshot - this should never happen :/")
            await ctx.response.send_message(embed=embed, ephemeral=True)  # Don't bother making a PaginationView
    else:  # We are viewing one command
        if str(ctx.guild.id) + '.' + query not in valid:
            error_embed = generate_simple_embed(f"That trigger (\"{query}\") doesn't exist in this server!",
                                                "Check your input.")
            await ctx.response.send_message(embed=error_embed, ephemeral=True)
            return
        creator_id = dict(watching_commands_access[str(ctx.guild.id) + '.' + query].find_one({"type": "meta"},
                                                                                             {"_id": False,
                                                                                              "type": False}))[
            "author"][1]
        trigger_access = dict(watching_commands_access[str(ctx.guild.id) + '.' + query].find_one({"type": "trigger"},
                                                                                                 {"_id": False,
                                                                                                  "type": False}))
        tracker_access = dict(watching_commands_access[str(ctx.guild.id) + '.' + query].find_one({"type": "tracker"},
                                                                                                 {"_id": False,
                                                                                                  "type": False}))
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
            u = await client.fetch_user(creator_id)
        actions = ''
        dropdown = TRIGGER_REQUIREMENTS[trigger_access['trigger_action_name']]['class']().dropdown_name()
        for action in list(watching_commands_access[str(ctx.guild.id) + '.' + query].find({"type": "do"}, {"_id": False,
                                                                                                           "type": False})):
            send_action = {}
            for a in action:
                send_action.update({a: await DiscordPickler.decode_object(action[a], ctx.guild)})
            actions += (":arrow_right:   " +
                        await DO_REQUIREMENTS[action["do_action_name"]]['class']
                        .human(send_action, dropdown) + '\n')
        actions = actions[:-1]
        if actions == '':
            actions = "There are no dos in this trigger!"
        embed.add_field(name="Created by:", value=u.mention)
        embed.add_field(name="Trigger type:", value=dropdown)
        embed.add_field(name="Dos:", value=actions, inline=False)
        embed.add_field(name="This trigger was activated:",
                        value=f"{total_triggered} time{pluralizer[0]} across {num_triggered} user{pluralizer[1]}.")
        embed.add_field(name="Description:", value=trigger_access['trigger_description'])
        embed.set_footer(text="Made with ❤ by @quantumbagel",
                         icon_url="https://avatars.githubusercontent.com/u/58365715")
        await ctx.response.send_message(embed=embed, ephemeral=True)


async def handle(id_type: str, creator: discord.Member = None, guild: discord.Guild = None, other=None):
    """
    Handle a generic trigger firing
    :param id_type: The type of the trigger
    :param creator: The discord.Member responsible for the action
    :param guild: The guild the command is in
    :param other: Other relevant data (passed through to Do.execute())
    :return: None
    """
    if creator.bot:  # Don't allow bots to activate anything
        log.debug("Ignoring bot creator.")
        return

    for database_id in [col for col in list(watching_commands_access.list_collection_names()) if
                        col.split('.')[0] == str(guild.id)]:  # Iterate through each command that this guild has
        trigger = database_id.split('.')[1]  # The command name
        trigger_dict = dict(watching_commands_access[str(guild.id)][trigger]
                            .find_one({"type": "trigger"}, {'_id': False, "type": False}))  # Trigger data
        submit_trigger_dict = {}
        for item in trigger_dict.keys():
            submit_trigger_dict.update({item: await DiscordPickler.decode_object(trigger_dict[item], guild)})
        if TRIGGER_REQUIREMENTS[submit_trigger_dict["trigger_action_name"]]["type"] == id_type:
            try:
                if await (TRIGGER_REQUIREMENTS[submit_trigger_dict["trigger_action_name"]]["class"]
                        .is_valid(submit_trigger_dict, other)):
                    watching_commands_access[database_id].update_one({"type": "tracker"},
                                                                     {"$inc": {str(creator.id): 1}})
                    pre_dos = list(watching_commands_access[str(guild.id)][trigger]
                                   .find({"type": "do"}, {'_id': False, 'type': False}))  # The do data from the DB

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
                    for identification in submit_dos:
                        # Compile the data together
                        data = {"do": identification, "dos": submit_dos, "trigger": submit_trigger_dict,
                                "meta": submit_meta,
                                "tracker": submit_tracker}
                        # Perform the execution
                        await (DO_REQUIREMENTS[identification["do_action_name"]]["class"]
                               .execute(data, client, guild, creator, other_discord_data=other))
            except KeyError as ke:
                log.warning(f"Failed is_valid check!\n{ke}")
                raise ke


@client.event
async def on_message(msg: discord.Message):
    """
    Handle the on_message trigger and redirect to handle()
    :param msg: The message
    :return: None
    """
    if msg.content == "triggered/sync" and msg.author.id == 897146430664355850:  # Performs sync
        await tree.sync()
        log.info("Performed authorized sync.")
        await msg.add_reaction("✅")  # leave confirmation
        return
    if msg.guild is None:
        return
    log.debug(f'Event "on_message" has been triggered! (server="{msg.guild.name}", server_id={msg.guild.id},'
              f' member={msg.author.global_name}, member_id={msg.author.id})')
    await handle("send_msg", msg.author, msg.guild, msg)


@client.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent):
    """
    Handle the reaction_add trigger and redirect to handle()
    :param ctx: The data from discord
    :return: None
    """
    event_guild = await client.fetch_guild(ctx.guild_id)
    log.debug(f'Event "reaction_add" has been triggered! (server="{event_guild.name}", server_id={event_guild.id},'
              f' member={ctx.member.global_name}, member_id={ctx.member.id})')
    await handle("reaction_add", ctx.member, event_guild, ctx.emoji)


@client.event
async def on_raw_reaction_remove(ctx: discord.RawReactionActionEvent):
    """
    Handle the reaction_remove trigger and redirect to handle()
    :param ctx: The data from discord
    :return: None
    """
    event_guild = await client.fetch_guild(ctx.guild_id)
    identity = ctx.user_id
    u_obj = event_guild.get_member(identity)
    if u_obj is None:
        u_obj = await event_guild.fetch_member(identity)
    log.debug(f'Event "reaction_remove" has been triggered! (server="{event_guild.name}", server_id={event_guild.id},'
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
    if before.channel != after.channel and after.channel is not None:
        log.debug(f'Event "vc_join" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                  f' member={member.global_name}, member_id={member.id})')
        await handle("vc_join", member, member.guild, [before, after])
    if before.channel != after.channel and after.channel is None:
        log.debug(f'Event "vc_leave" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
                  f' member={member.global_name}, member_id={member.id})')
        await handle("vc_leave", member, member.guild, [before, after])


@client.event
async def on_member_join(member: discord.Member):
    """
    Call handle with the "member_join" event
    :param member: The member who joined
    :return: None
    """
    log.debug(f'Event "member_join" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
              f' member={member.global_name}, member_id={member.id})')
    await handle("member_join", member, member.guild)


@client.event
async def on_member_remove(member: discord.Member):
    """
    Call handle with the "member_leave" event
    :param member: The member who left :(
    :return: None
    """
    log.debug(f'Event "member_leave" has been triggered! (server={member.guild.name}, server_id={member.guild.id},'
              f' member={member.global_name}, member_id={member.id})')
    await handle("member_leave", member, member.guild)


@client.event
async def on_guild_join(guild: discord.Guild):
    """
    Send a message to guilds when the bot is added.
    :param guild: the guild the bot was added to
    :return: nothing
    """
    log.info("Added to guild \"" + guild.name + f"\"! (id={guild.id})")
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
                    value="Please read the [README](https://github.com/quantumbagel/Triggered/blob/master/README.md) or"
                          "for command usage :D")
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

    # Make sure to send in the system channel - if there is none, nothing *should* be sent
    await guild.system_channel.send(embed=embed)


@client.event
async def on_guild_leave(guild: discord.Guild):
    """
    Purge data from guilds we were kicked from.
    :param guild: The guild we were removed from
    :return: nothing
    """
    log.info(f"Dropping all triggers from guild \"{guild.name}\" (id={guild.id})")
    valid = [col for col in list(watching_commands_access.list_collection_names()) if
             col.split('.')[0] == str(guild.id)]
    for command_to_remove in valid:
        watching_commands_access.drop_collection(command_to_remove)
    log.info(f"Dropped {len(valid)} commands.")


try:
    tree.add_command(triggered)
    client.run(BOT_SECRET)
except Exception as e:
    log.critical(f"Critical error: {str(e)}")
    log.critical("This is likely due to:\n1. Internet issues\n2. Incorrect discord token\n3. Incorrectly set up "
                 "discord bot")
