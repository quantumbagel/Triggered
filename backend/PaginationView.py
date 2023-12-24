import discord
import math
import logging


class PaginationView(discord.ui.View):
    current_page: int = 1
    sep: int = 3

    def __init__(self, timeout=None, title="", data: list[dict[str, str]] = None, author: discord.Member = None,
                 embed_color: discord.Color = None):
        """
        Initialize a PaginationView
        :param timeout: the timeout (honestly not sure lol)
        :param title: The title of the View
        :param embed_color: The color of the embed
        :param data: The data to store
        :param author: the author of the message.
        """
        super().__init__(timeout=timeout)
        self.title = title
        self.author = author
        self.data = data
        self.message = None
        self.embed_color = embed_color
        self.logger = logging.getLogger("triggered").getChild("pview")

    async def send(self, ctx: discord.Interaction):
        """
        Send the view in a message
        :param ctx: the Interaction
        :return:
        """
        try:
            await ctx.response.send_message(view=self)
        except discord.NotFound:
            (self.logger.getChild("send")
             .error("Unknown interaction! This is probably due to the bot just coming back online."))
            return  # Fail the interaction
        self.message = await ctx.original_response()
        await self.update_message(self.data[:self.sep])

    def create_embed(self, data):
        """
        Generate the embed with per-page data
        :param data: the data to parse
        :return: the embed
        """
        embed = discord.Embed(title=f"{self.title} (page {self.current_page}/{math.ceil(len(self.data) / self.sep)})",
                              color=self.embed_color)

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
        self.logger.getChild("update_message").debug("Successfully updated existing interaction!")

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
