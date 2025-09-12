import discord
from discord.ext import commands
from typing import Union, Tuple


class EmbedCustomizer:
    def __init__(self, source: Union[commands.Context, discord.Interaction, discord.TextChannel,
                                     discord.DMChannel, discord.User, discord.Member, discord.Message]):
        self.source = source
        self.default_colour = 0x7289DA

        if isinstance(source, discord.Interaction):
            self.user = source.user
            self.guild = source.guild
            self.bot = getattr(source, 'client', None)
        elif isinstance(source, commands.Context):
            self.user = source.author
            self.guild = source.guild
            self.bot = getattr(source, 'bot', None)
        elif isinstance(source, discord.Message):
            self.user = source.author
            self.guild = source.guild
            self.bot = getattr(source, 'bot', None) or getattr(
                getattr(source, "_state", None), "_get_client", lambda: None
            )()
        elif isinstance(source, (discord.User, discord.Member)):
            self.user = source
            self.guild = getattr(source, 'guild', None)
            self.bot = None
        else:
            self.user = None
            self.guild = None
            self.bot = None

    def _get_custom_value(self, method_name: str, default_value: str = "") -> str:
        if self.bot and hasattr(self.bot, method_name):
            if self.user and self.guild:
                return getattr(self.bot, method_name)(self.user.id, self.guild.id)
            elif self.user:
                return getattr(self.bot, method_name)(self.user.id)
        return default_value

    def get_embed_colour(self, color: Union[discord.Colour, int] = None, colour: Union[discord.Colour, int] = None) -> Union[discord.Colour, int]:
        if colour is not None or color is not None:
            return color if color is not None else colour
        return self._get_custom_value('get_embed_colour', self.default_colour)

    def get_author_name(self, author_name: str = "Cheap Credits") -> str:
        if author_name == "Cheap Credits":
            return self._get_custom_value('get_embed_author_name', author_name)
        return author_name

    def get_author_icon(self, author_icon_url: str = "") -> str:
        if not author_icon_url:
            return self._get_custom_value('get_embed_author_icon', author_icon_url)
        return author_icon_url

    def get_footer_text(self, footer_text: str = "") -> str:
        if not footer_text:
            return self._get_custom_value('get_embed_footer_text', footer_text)
        return footer_text

    def get_footer_icon(self, footer_icon_url: str = "") -> str:
        if not footer_icon_url:
            return self._get_custom_value('get_embed_footer_icon', footer_icon_url)
        return footer_icon_url

    def get_all_custom_values(self,
                              color: Union[discord.Colour, int] = None,
                              colour: Union[discord.Colour, int] = None,
                              author_name: str = "Cheap Credits",
                              author_icon_url: str = "",
                              footer_text: str = "",
                              footer_icon_url: str = "") -> Tuple:
        return (
            self.get_embed_colour(color, colour),
            self.get_author_name(author_name),
            self.get_author_icon(author_icon_url),
            self.get_footer_text(footer_text),
            self.get_footer_icon(footer_icon_url)
        )
