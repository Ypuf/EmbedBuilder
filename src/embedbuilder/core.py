import discord
from discord.ext import commands
import datetime
import os
import asyncio
import logging
from pytz import timezone
from typing import Union, List

from .customization import EmbedCustomizer
from .pagination import PaginationView
from .utils import chunk_text, truncate_text

logger = logging.getLogger("EmbedBuilder")


class EmbedBuilder:
    def __init__(self, source: Union[commands.Context, discord.Interaction, discord.TextChannel, discord.DMChannel, discord.User, discord.Member, discord.Message]):
        self.source = source
        self.customizer = EmbedCustomizer(source)

        # Core embed properties
        self._title = ""
        self._description = ""
        self._color = None
        self._url = ""
        self._timestamp = None

        # Author properties
        self._author_name = ""
        self._author_icon_url = ""
        self._author_url = ""

        # Footer properties
        self._footer_text = ""
        self._footer_icon_url = ""

        # Media properties
        self._thumbnail_url = ""
        self._image_url = ""

        # Content and messaging properties
        self._content = ""
        self._fields = []
        self._files = []
        self._file_path = None

        # Behavior properties
        self._reply = True
        self._ephemeral = False
        self._delete_after = None
        self._view = None
        self._allowed_mentions = None
        self._tts = False
        self._suppress_embeds = False
        self._silent = False
        self._mention_author = False
        self._stickers = []

        # Advanced properties
        self._max_embeds = 10
        self._embed_color_gradient = False
        self._timezone_str = 'UTC'
        self._paginated = False
        self._pages = []
        self._pagination_timeout = 180.0
        self._edit_message = None
        self._override_user = None

    def set_title(self, title: str) -> "EmbedBuilder":
        """Set the embed title."""
        self._title = str(title)
        return self

    def set_description(self, description: str) -> "EmbedBuilder":
        """Set the embed description."""
        self._description = str(description)
        return self

    def set_color(self, color: Union[discord.Colour, int]) -> "EmbedBuilder":
        """Set the embed color."""
        self._color = color
        return self

    def set_colour(self, colour: Union[discord.Colour, int]) -> "EmbedBuilder":
        """Set the embed colour (alias for set_color)."""
        return self.set_color(colour)

    def set_url(self, url: str) -> "EmbedBuilder":
        """Set the embed URL."""
        self._url = str(url) if url else ""
        return self

    def set_timestamp(self, timestamp: datetime.datetime = None) -> "EmbedBuilder":
        """Set the embed timestamp. If None, uses current time."""
        self._timestamp = timestamp
        return self

    def set_author(self, name: str = None, icon_url: str = "", url: str = "") -> "EmbedBuilder":
        """Set the embed author."""
        if name is not None:
            self._author_name = str(name)
        if icon_url:
            self._author_icon_url = str(icon_url)
        if url:
            self._author_url = str(url)
        return self

    def set_footer(self, text: str = None, icon_url: str = "") -> "EmbedBuilder":
        """Set the embed footer."""
        if text is not None:
            self._footer_text = str(text)
        if icon_url:
            self._footer_icon_url = str(icon_url)
        return self

    def set_thumbnail(self, url: str) -> "EmbedBuilder":
        """Set the embed thumbnail."""
        self._thumbnail_url = str(url) if url else ""
        return self

    def set_image(self, url: str) -> "EmbedBuilder":
        """Set the embed image."""
        self._image_url = str(url) if url else ""
        return self

    def add_field(self, name: str, value: str, inline: bool = False) -> "EmbedBuilder":
        """Add a field to the embed."""
        self._fields.append((str(name), str(value), inline))
        return self

    def set_content(self, content: str) -> "EmbedBuilder":
        """Set the message content (separate from embed)."""
        self._content = str(content)
        return self

    def add_file(self, file: discord.File) -> "EmbedBuilder":
        """Add a file to the message."""
        self._files.append(file)
        return self

    def set_file_path(self, file_path: str) -> "EmbedBuilder":
        """Set a file path to attach."""
        self._file_path = str(file_path) if file_path else None
        return self

    def set_reply(self, reply: bool = True) -> "EmbedBuilder":
        """Set whether to reply to the source message."""
        self._reply = reply
        return self

    def set_ephemeral(self, ephemeral: bool = True) -> "EmbedBuilder":
        """Set whether the message should be ephemeral (for interactions)."""
        self._ephemeral = ephemeral
        return self

    def set_delete_after(self, seconds: float) -> "EmbedBuilder":
        """Set auto-delete timeout."""
        self._delete_after = seconds
        return self

    def set_view(self, view: discord.ui.View) -> "EmbedBuilder":
        """Set a Discord UI view."""
        self._view = view
        return self

    def set_allowed_mentions(self, allowed_mentions: discord.AllowedMentions) -> "EmbedBuilder":
        """Set allowed mentions."""
        self._allowed_mentions = allowed_mentions
        return self

    def enable_pagination(self, timeout: float = 180.0) -> "EmbedBuilder":
        """Enable pagination for long descriptions."""
        self._paginated = True
        self._pagination_timeout = timeout
        return self

    def add_page(self, title: str = "", description: str = "", **kwargs) -> "EmbedBuilder":
        """Add a custom page for pagination."""
        page = {
            "title": title,
            "description": description,
            **kwargs
        }
        self._pages.append(page)
        return self

    def set_timezone(self, timezone_str: str) -> "EmbedBuilder":
        """Set the timezone for timestamps."""
        self._timezone_str = timezone_str
        return self

    def enable_gradient_colors(self, enabled: bool = True) -> "EmbedBuilder":
        """Enable color gradient for multiple embeds."""
        self._embed_color_gradient = enabled
        return self

    def set_max_embeds(self, max_embeds: int) -> "EmbedBuilder":
        """Set maximum number of embeds to create."""
        self._max_embeds = max_embeds
        return self

    def edit_message(self, message: discord.Message) -> "EmbedBuilder":
        """Set a message to edit instead of sending new."""
        self._edit_message = message
        return self

    def override_user(self, user: Union[discord.Member, discord.User]) -> "EmbedBuilder":
        """Override the user for customization purposes."""
        self._override_user = user
        return self

    async def build_embed(self, chunk: str = None, index: int = 0, total_chunks: int = 1) -> discord.Embed:
        """Build a single Discord embed."""
        customizer = EmbedCustomizer(self._override_user or self.source)
        (custom_colour, custom_author_name, custom_author_icon,
         custom_footer_text, custom_footer_icon) = customizer.get_all_custom_values(
            color=self._color,
            author_name=self._author_name,
            author_icon_url=self._author_icon_url,
            footer_text=self._footer_text,
            footer_icon_url=self._footer_icon_url
        )

        title = self._title
        if total_chunks > 1 and index > 0:
            title = f"{self._title} (continued {index + 1}/{total_chunks})"
        title = truncate_text(title, 256)

        description = chunk if chunk is not None else self._description

        embed_color = (
            discord.Colour.from_hsv(index / total_chunks, 1, 1)
            if self._embed_color_gradient and total_chunks > 1
            else custom_colour
        )

        if self._timestamp is None:
            try:
                tz = timezone(self._timezone_str)
                timestamp = datetime.datetime.now(tz)
            except Exception:
                timestamp = datetime.datetime.now()
        else:
            timestamp = self._timestamp

        embed = discord.Embed(
            title=title,
            description=description,
            colour=embed_color,
            url=self._url if (index == 0 and self._url) else None,
            timestamp=timestamp
        )

        if index == 0 and custom_author_name:
            author_name = truncate_text(custom_author_name, 256)
            embed.set_author(
                name=author_name,
                icon_url=custom_author_icon or None,
                url=self._author_url or None
            )

        if index == 0 and self._thumbnail_url:
            embed.set_thumbnail(url=self._thumbnail_url)

        if index == 0:
            if self._file_path:
                embed.set_image(url="attachment://image.png")
            elif self._image_url:
                embed.set_image(url=self._image_url)

        if index == 0 and self._fields:
            for name, value, inline in self._fields:
                name = truncate_text(name, 256)
                value = truncate_text(value, 1024)
                embed.add_field(name=name, value=value, inline=inline)

        if custom_footer_text:
            footer_text = truncate_text(custom_footer_text, 2048)
            embed.set_footer(text=footer_text,
                             icon_url=custom_footer_icon or None)

        return embed

    async def send(self) -> List[discord.Message]:
        """Send the embed(s) and return the message(s)."""
        if not self._author_name or not isinstance(self._author_name, str):
            raise ValueError("Author name must be a non-empty string")

        if len(self._title) > 256:
            raise ValueError(
                f"Title length ({len(self._title)}) exceeds Discord's limit of 256 characters")

        if self._content and len(self._content) > 2000:
            raise ValueError(
                f"Content length ({len(self._content)}) exceeds Discord's limit of 2000 characters")

        if self._file_path and not os.path.exists(self._file_path):
            raise ValueError(f"File not found at path: {self._file_path}")

        is_interaction = isinstance(self.source, discord.Interaction)
        is_ctx = isinstance(self.source, commands.Context)

        if isinstance(self.source, (discord.User, discord.Member)):
            self.source = await self.source.create_dm()
        elif isinstance(self.source, discord.Message):
            self.source = self.source.channel

        channel = (
            self.source if isinstance(self.source, (discord.TextChannel, discord.DMChannel))
            else getattr(self.source, 'channel', None)
        )

        if not channel and not is_interaction and not self._edit_message:
            raise ValueError("Could not determine target channel")

        if self._paginated and self._pages:
            return await self._send_paginated()

        if len(self._description) <= 4096:
            chunks = [self._description]
        else:
            chunks = chunk_text(
                self._description, max_chunk_size=4096, max_chunks=self._max_embeds)

        if len(chunks) == 1 and not self._edit_message:
            return await self._send_single_embed(chunks[0])
        else:
            return await self._send_multiple_embeds(chunks)

    async def _send_single_embed(self, description: str) -> List[discord.Message]:
        embed = await self.build_embed(description, 0, 1)

        discord_files = []
        if self._file_path:
            discord_files.append(discord.File(
                self._file_path, filename=os.path.basename(self._file_path)))
        discord_files.extend(self._files)

        message_options = {
            "embed": embed,
            "allowed_mentions": self._allowed_mentions,
            "tts": self._tts,
            "suppress_embeds": self._suppress_embeds,
            "silent": self._silent,
        }

        if self._content:
            message_options["content"] = self._content
        if discord_files:
            message_options["files"] = discord_files
        if self._view:
            message_options["view"] = self._view

        if self._edit_message:
            if discord_files:
                try:
                    await self._edit_message.delete()
                    self._edit_message = None
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    self._edit_message = None
            else:
                try:
                    await self._edit_message.edit(**message_options)
                    return [self._edit_message]
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    self._edit_message = None

        if isinstance(self.source, discord.Interaction):
            message_options.update({
                "ephemeral": self._ephemeral,
                "delete_after": self._delete_after,
            })

            if not self.source.response.is_done():
                await self.source.response.send_message(**message_options)
                message = await self.source.original_response()
            else:
                message = await self.source.followup.send(**message_options)
        else:
            message_options.update({
                "delete_after": self._delete_after,
                "stickers": self._stickers,
                "mention_author": self._mention_author,
            })

            if isinstance(self.source, commands.Context) and self._reply:
                message = await self.source.reply(**message_options)
            else:
                channel = (
                    self.source if isinstance(self.source, (discord.TextChannel, discord.DMChannel))
                    else self.source.channel
                )
                message = await channel.send(**message_options)

        return [message]

    async def _send_multiple_embeds(self, chunks: List[str]) -> List[discord.Message]:
        """Send multiple embeds for long descriptions."""
        messages = []

        if self._edit_message:
            try:
                await self._edit_message.delete()
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                pass
            self._edit_message = None

        for i, chunk in enumerate(chunks):
            try:
                embed = await self.build_embed(chunk, i, len(chunks))

                message_options = {
                    "embed": embed,
                    "allowed_mentions": self._allowed_mentions,
                    "tts": self._tts,
                    "suppress_embeds": self._suppress_embeds,
                    "silent": self._silent,
                }

                if i == 0:
                    if self._content:
                        message_options["content"] = self._content

                    discord_files = []
                    if self._file_path:
                        discord_files.append(discord.File(
                            self._file_path, filename=os.path.basename(self._file_path)))
                    discord_files.extend(self._files)

                    if discord_files:
                        message_options["files"] = discord_files
                    if self._view:
                        message_options["view"] = self._view

                if isinstance(self.source, discord.Interaction):
                    message_options["ephemeral"] = self._ephemeral

                    if i == 0 and not self.source.response.is_done():
                        await self.source.response.send_message(**message_options)
                        message = await self.source.original_response()
                    else:
                        message = await self.source.followup.send(**message_options)
                else:
                    if i == 0:
                        message_options.update({
                            "delete_after": self._delete_after,
                            "stickers": self._stickers,
                            "mention_author": self._mention_author,
                        })

                    if isinstance(self.source, commands.Context) and self._reply and i == 0:
                        message = await self.source.reply(**message_options)
                    else:
                        channel = (
                            self.source if isinstance(self.source, (discord.TextChannel, discord.DMChannel))
                            else self.source.channel
                        )
                        message = await channel.send(**message_options)

                messages.append(message)

                if i < len(chunks) - 1:
                    await asyncio.sleep(0.5)

            except discord.HTTPException as e:
                logger.error(f"Error sending embed {i+1}/{len(chunks)}: {e}")
                if not messages:
                    raise

        return messages

    async def _send_paginated(self) -> List[discord.Message]:
        """Send paginated embeds."""
        if not self._pages:
            raise ValueError(
                "Pages list must be provided when paginated is True")

        embeds = []
        discord_files = []

        for i, page in enumerate(self._pages):
            page_title = page.get(
                'title', f"{self._title} (Page {i+1}/{len(self._pages)})")
            page_title = truncate_text(page_title, 256)

            page_description = page.get('description', '')
            if not page_description:
                raise ValueError(f"Description for page {i+1} cannot be empty")

            page_color = page.get('colour', page.get('color', self._color))

            embed = discord.Embed(
                title=page_title,
                description=page_description,
                colour=page_color,
                url=page.get('url', self._url if i == 0 else ""),
                timestamp=self._timestamp or datetime.datetime.now()
            )

            if i == 0 or page.get('author_name'):
                author_name = page.get('author_name', self._author_name)
                if author_name:
                    embed.set_author(
                        name=truncate_text(author_name, 256),
                        icon_url=page.get('author_icon_url',
                                          self._author_icon_url) or None,
                        url=page.get('author_url', self._author_url) or None
                    )

            if page.get('thumbnail_url'):
                embed.set_thumbnail(url=page['thumbnail_url'])
            elif i == 0 and self._thumbnail_url:
                embed.set_thumbnail(url=self._thumbnail_url)

            if page.get('file_path'):
                embed.set_image(url=f"attachment://image_{i}.png")
                if os.path.exists(page['file_path']):
                    discord_files.append(discord.File(
                        page['file_path'], filename=f'image_{i}.png'))
            elif page.get('image_url'):
                embed.set_image(url=page['image_url'])
            elif i == 0 and self._image_url:
                embed.set_image(url=self._image_url)

            page_fields = page.get('fields', self._fields if i == 0 else None)
            if page_fields:
                for name, value, inline in page_fields:
                    embed.add_field(
                        name=truncate_text(name, 256),
                        value=truncate_text(value, 1024),
                        inline=inline
                    )

            footer_text = page.get('footer_text', self._footer_text)
            if footer_text:
                embed.set_footer(
                    text=truncate_text(footer_text, 2048),
                    icon_url=page.get('footer_icon_url',
                                      self._footer_icon_url) or None
                )

            embeds.append(embed)

        if self._file_path and os.path.exists(self._file_path):
            discord_files.append(discord.File(
                self._file_path, filename='image_0.png'))

        discord_files.extend(self._files)

        pagination_view = PaginationView(
            embeds, timeout=self._pagination_timeout)

        message_options = {
            "embed": embeds[0],
            "view": pagination_view,
            "allowed_mentions": self._allowed_mentions,
        }

        if self._content:
            message_options["content"] = self._content
        if discord_files:
            message_options["files"] = discord_files

        if self._edit_message:
            if discord_files:
                try:
                    await self._edit_message.delete()
                    self._edit_message = None
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    self._edit_message = None
            else:
                try:
                    await self._edit_message.edit(**message_options)
                    return [self._edit_message]
                except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                    self._edit_message = None

        if isinstance(self.source, discord.Interaction):
            message_options.update({
                "ephemeral": self._ephemeral,
                "tts": self._tts,
                "suppress_embeds": self._suppress_embeds,
                "silent": self._silent,
            })

            if not self.source.response.is_done():
                await self.source.response.send_message(**message_options)
                message = await self.source.original_response()
            else:
                message = await self.source.followup.send(**message_options)
        else:
            message_options.update({
                "tts": self._tts,
                "suppress_embeds": self._suppress_embeds,
                "silent": self._silent,
            })

            if isinstance(self.source, commands.Context) and self._reply:
                message = await self.source.reply(**message_options)
            else:
                channel = (
                    self.source if isinstance(self.source, (discord.TextChannel, discord.DMChannel))
                    else self.source.channel
                )
                message = await channel.send(**message_options)

        return [message]
