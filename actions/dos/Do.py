import abc
import discord


class Do(abc.ABC):
    @abc.abstractmethod
    async def human(variables: dict, trigger_id: str):
        pass

    @abc.abstractmethod
    async def execute(variables: dict, full_var: dict, trigger_id: str, trigger_name: str, client, guild: discord.Guild,
                      author: discord.Member, other_discord_data=None):
        pass

    @abc.abstractmethod
    def dropdown_name(self):
        pass
