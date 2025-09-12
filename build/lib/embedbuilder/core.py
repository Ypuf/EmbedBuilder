import discord
from discord.ext import commands
import datetime
import logging
from typing import Union, List

from .utils import chunk_text
from .messagesender import MessageSender, SourceManager
from .confighandlers import EmbedConfig, MessageConfig, ThreadConfig, PaginationConfig

logger = logging.getLogger("EmbedBuilder")


class EmbedBuilder:
    def __init__(self, source: Union[commands.Context, discord.Interaction, discord.TextChannel, discord.DMChannel, discord.ForumChannel, discord.Thread, discord.User, discord.Member, discord.Message]):
        self.source = source
        self.embed_config = EmbedConfig()
        self.message_config = MessageConfig()
        self.pagination_config = PaginationConfig()
        self.thread_config = ThreadConfig()
        self.override_user = None

    def set_title(self, title: str) -> "EmbedBuilder":
        self.embed_config.set_title(title)
        return self

    def set_description(self, description: str) -> "EmbedBuilder":
        self.embed_config.set_description(description)
        return self

    def set_color(self, color: Union[discord.Colour, int]) -> "EmbedBuilder":
        self.embed_config.set_color(color)
        return self

    def set_colour(self, colour: Union[discord.Colour, int]) -> "EmbedBuilder":
        return self.set_color(colour)

    def set_url(self, url: str) -> "EmbedBuilder":
        self.embed_config.set_url(url)
        return self

    def set_timestamp(self, timestamp: datetime.datetime = None) -> "EmbedBuilder":
        self.embed_config.set_timestamp(timestamp)
        return self

    def set_author(self, name: str = None, icon_url: str = "", url: str = "") -> "EmbedBuilder":
        self.embed_config.set_author(name, icon_url, url)
        return self

    def set_footer(self, text: str = None, icon_url: str = "") -> "EmbedBuilder":
        self.embed_config.set_footer(text, icon_url)
        return self

    def set_thumbnail(self, url: str) -> "EmbedBuilder":
        self.embed_config.set_thumbnail(url)
        return self

    def set_image(self, url: str) -> "EmbedBuilder":
        self.embed_config.set_image(url)
        return self

    def add_field(self, name: str, value: str, inline: bool = False) -> "EmbedBuilder":
        self.embed_config.add_field(name, value, inline)
        return self

    def add_fields(self, fields: List[tuple]) -> "EmbedBuilder":
        self.embed_config.add_fields(fields)
        return self

    def set_timezone(self, timezone_str: str) -> "EmbedBuilder":
        self.embed_config.set_timezone(timezone_str)
        return self

    def enable_gradient_colors(self, enabled: bool = True) -> "EmbedBuilder":
        self.embed_config.enable_gradient_colors(enabled)
        return self

    def set_content(self, content: str) -> "EmbedBuilder":
        self.message_config.set_content(content)
        return self

    def add_file(self, file: discord.File) -> "EmbedBuilder":
        self.message_config.add_file(file)
        return self

    def set_file_path(self, file_path: str) -> "EmbedBuilder":
        self.message_config.set_file_path(file_path)
        return self

    def set_reply(self, reply: bool = True) -> "EmbedBuilder":
        self.message_config.set_reply(reply)
        return self

    def set_ephemeral(self, ephemeral: bool = True) -> "EmbedBuilder":
        self.message_config.set_ephemeral(ephemeral)
        return self

    def set_delete_after(self, seconds: float) -> "EmbedBuilder":
        self.message_config.set_delete_after(seconds)
        return self

    def set_view(self, view: discord.ui.View) -> "EmbedBuilder":
        self.message_config.set_view(view)
        return self

    def set_allowed_mentions(self, allowed_mentions: discord.AllowedMentions) -> "EmbedBuilder":
        self.message_config.set_allowed_mentions(allowed_mentions)
        return self

    def set_max_embeds(self, max_embeds: int) -> "EmbedBuilder":
        self.message_config.set_max_embeds(max_embeds)
        return self

    def edit_message(self, message: discord.Message) -> "EmbedBuilder":
        self.message_config.edit_message(message)
        return self

    def override_user(self, user: Union[discord.Member, discord.User]) -> "EmbedBuilder":
        self.override_user = user
        return self

    def enable_pagination(self, timeout: float = 180.0) -> "EmbedBuilder":
        self.pagination_config.enable(timeout)
        return self

    def add_page(self, title: str = "", description: str = "", **kwargs) -> "EmbedBuilder":
        self.pagination_config.add_page(title, description, **kwargs)
        return self

    def create_thread(self, name: str, auto_archive_duration: int = 1440, reason: str = None) -> "EmbedBuilder":
        self.thread_config.enable_thread_creation(
            name, auto_archive_duration, reason)
        return self

    def create_forum_thread(self, name: str, content: str = None) -> "EmbedBuilder":
        self.thread_config.set_forum_thread(name, content)
        return self

    async def send(self) -> List[discord.Message]:
        if not self.embed_config.author_name or not isinstance(self.embed_config.author_name, str):
            raise ValueError("Author name must be a non-empty string")

        if len(self.embed_config.title) > 256:
            raise ValueError(
                f"Title length ({len(self.embed_config.title)}) exceeds Discord's limit of 256 characters")

        self.message_config.validate()

        source = await SourceManager.prepare_source(self.source)
        source = await SourceManager.handle_forum_thread(source, self.thread_config, self.message_config)

        channel = (
            source if isinstance(source, (discord.TextChannel, discord.DMChannel, discord.Thread))
            else getattr(source, 'channel', None)
        )

        if not channel and not isinstance(source, discord.Interaction) and not self.message_config.edit_message:
            raise ValueError("Could not determine target channel")

        sender = MessageSender(source, self.embed_config,
                               self.message_config, self.thread_config)
        if self.override_user:
            sender.set_override_user(self.override_user)

        if self.pagination_config.is_enabled():
            return await sender.send_paginated(self.pagination_config)

        if len(self.embed_config.description) <= 4096:
            chunks = [self.embed_config.description]
        else:
            chunks = chunk_text(
                self.embed_config.description,
                max_chunk_size=4096,
                max_chunks=self.message_config.max_embeds
            )

        if len(chunks) == 1 and not self.message_config.edit_message:
            return await sender.send_single_embed(chunks[0])
        else:
            return await sender.send_multiple_embeds(chunks)
