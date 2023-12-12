import abc
import discord


class Trigger(abc.ABC):
    @abc.abstractmethod
    async def human(variables: dict):
        """
        Return a human-readable repr of the Trigger
        :return:
        """
        pass

    @abc.abstractmethod
    async def is_valid(variables: dict, discord_object: discord.Object):
        """
        Return if the Trigger has fired
        :param discord_object: The message / channel / voice state
        :return: True or False
        """
        pass

    @abc.abstractmethod
    def dropdown_name(self):
        """
        Return a formatted name for the bot's choices (e.x. Contains Text)
        :return: the formatted name
        """
        pass
