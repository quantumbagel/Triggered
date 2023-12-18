import abc
import discord


class Do(abc.ABC):
    @abc.abstractmethod
    async def human(variables: dict, trigger_id: str) -> str:
        """
        Take the variables and the trigger_id
        :param variables: the variable data about the do to humanize
        :param trigger_id: the trigger ID
        :return:
        """
        pass

    @abc.abstractmethod
    async def execute(data: dict, client, guild: discord.Guild, author: discord.Member, other_discord_data=None) -> None:
        """
        Perform the do action. You get a multitude of data to perform this.
        :param client:
        :param guild:
        :param author:
        :param other_discord_data:
        :return:
        """
        pass

    @abc.abstractmethod
    def dropdown_name(self) -> str:
        """
        Return the name that should show on the dropdown
        :return:
        """
        pass
