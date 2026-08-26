import logging
import math

import discord

from backend.ui import runtime
from backend.ui.compiler import Compiler
from backend.ui.emoji import EmojiResolver
from backend.ui.message import edit_view, send_view
from backend.ui.panels import build_list_page_view


def page_slice(data: list, current_page: int, sep: int) -> list:
    """Return the slice of data that belongs on current_page (1-indexed)."""
    if current_page < 1 or sep < 1:
        return []
    from_item = (current_page - 1) * sep
    return data[from_item:from_item + sep]


class PaginationView:
    def __init__(
        self,
        timeout=None,
        title="",
        data: list[dict[str, str]] | None = None,
        author: discord.Member = None,
        embed_color: discord.Color = None,
        compiler: Compiler | None = None,
        emoji: EmojiResolver | None = None,
        sep: int = 3,
    ):
        """
        Paginate trigger list rows as a Components V2 layout.
        """
        self.current_page = 1
        self.sep = sep
        self.title = title
        self.author = author
        self.data = data or []
        self.message = None
        self.embed_color = embed_color
        self.compiler = compiler
        self.emoji = emoji
        self.logger = logging.getLogger("triggered").getChild("pview")

    def _compiler(self) -> Compiler:
        if self.compiler is not None:
            return self.compiler
        if runtime.compiler is None:
            raise RuntimeError("UI compiler is not configured")
        return runtime.compiler

    def _emoji(self) -> EmojiResolver:
        if self.emoji is not None:
            return self.emoji
        if runtime.emoji is None:
            raise RuntimeError("UI emoji resolver is not configured")
        return runtime.emoji

    def _pages(self) -> int:
        if not self.data:
            return 1
        return max(1, math.ceil(len(self.data) / self.sep))

    def get_current_page_data(self) -> list[dict[str, str]]:
        return page_slice(self.data, self.current_page, self.sep)

    def _layout(self):
        return build_list_page_view(
            emoji=self._emoji(),
            title=self.title,
            page=self.current_page,
            pages=self._pages(),
            items=self.get_current_page_data(),
        )

    async def _on_action(
        self,
        interaction: discord.Interaction,
        source: str,
        payload: dict | None,
        values: list[str] | None,
    ) -> None:
        if self.author is not None and interaction.user.id != self.author.id:
            await interaction.response.defer()
            return
        pages = self._pages()
        if source == "first":
            self.current_page = 1
        elif source == "prev":
            self.current_page = max(1, self.current_page - 1)
        elif source == "next":
            self.current_page = min(pages, self.current_page + 1)
        elif source == "last":
            self.current_page = pages
        await edit_view(
            interaction, self._layout(), on_action=self._on_action, compiler=self._compiler()
        )
        self.logger.getChild("update_message").debug("Successfully updated existing interaction!")

    async def send(self, ctx: discord.Interaction):
        """
        Send the view in a message
        :param ctx: the Interaction
        :return:
        """
        try:
            self.message = await send_view(
                ctx, self._layout(), on_action=self._on_action, compiler=self._compiler()
            )
        except discord.NotFound:
            (self.logger.getChild("send")
             .error("Unknown interaction! This is probably due to the bot just coming back online."))
            return
