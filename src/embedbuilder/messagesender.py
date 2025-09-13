import discord
from discord.ext import commands
from typing import Union, List, Optional
import logging

logger = logging.getLogger("MessageSender")


class MessageSender:
    """Handles the actual sending of Discord messages with embeds."""

    def __init__(self, source: Union[commands.Context, discord.Interaction, discord.TextChannel, discord.DMChannel, discord.Thread, discord.User, discord.Member, discord.Message]):
        self.source = source
        self._setup_source_info()

    def _setup_source_info(self):
        """Extract relevant information from the source object."""
        if isinstance(self.source, discord.Interaction):
            self.is_interaction = True
            self.is_context = False
            self.channel = self.source.channel
            self.user = self.source.user
        elif isinstance(self.source, commands.Context):
            self.is_interaction = False
            self.is_context = True
            self.channel = self.source.channel
            self.user = self.source.author
        elif isinstance(self.source, (discord.User, discord.Member)):
            self.is_interaction = False
            self.is_context = False
            self.channel = None  # Will create DM
            self.user = self.source
        elif isinstance(self.source, discord.Message):
            self.is_interaction = False
            self.is_context = False
            self.channel = self.source.channel
            self.user = self.source.author
        else:
            self.is_interaction = False
            self.is_context = False
            self.channel = self.source
            self.user = None

    async def _prepare_channel(self) -> discord.abc.Messageable:
        """Ensure we have a valid channel to send to."""
        if self.channel is None and self.user:
            return await self.user.create_dm()
        return self.channel or self.source

    def _build_message_options(self, embed: discord.Embed, content: str = None, files: List[discord.File] = None, view: discord.ui.View = None, **kwargs) -> dict:
        """Build the message options dictionary."""
        options = {
            "embed": embed,
            "allowed_mentions": kwargs.get("allowed_mentions"),
            "tts": kwargs.get("tts", False),
            "suppress_embeds": kwargs.get("suppress_embeds", False),
            "silent": kwargs.get("silent", False),
        }

        if content:
            options["content"] = content
        if files:
            options["files"] = files
        if view:
            options["view"] = view

        if self.is_interaction:
            options.update({
                "ephemeral": kwargs.get("ephemeral", False),
                "delete_after": kwargs.get("delete_after"),
            })
        else:
            options.update({
                "delete_after": kwargs.get("delete_after"),
                "stickers": kwargs.get("stickers", []),
                "mention_author": kwargs.get("mention_author", False),
            })

        return {k: v for k, v in options.items() if v is not None}

    async def send_message(self, embed: discord.Embed, content: str = None, files: List[discord.File] = None, view: discord.ui.View = None, reply: bool = True, **kwargs) -> discord.Message:
        """Send a single message with embed."""
        channel = await self._prepare_channel()
        options = self._build_message_options(
            embed, content, files, view, **kwargs)

        if self.is_interaction:
            return await self._send_interaction_message(options)
        elif self.is_context and reply:
            return await self.source.reply(**options)
        else:
            return await channel.send(**options)

    async def _send_interaction_message(self, options: dict) -> discord.Message:
        """Handle interaction-specific message sending."""
        if not self.source.response.is_done():
            await self.source.response.send_message(**options)
            return await self.source.original_response()
        else:
            return await self.source.followup.send(**options)

    async def edit_message(self, message: discord.Message, embed: discord.Embed, content: str = None, files: List[discord.File] = None, view: discord.ui.View = None, **kwargs) -> discord.Message:
        if files:
            try:
                await message.delete()
                return await self.send_message(embed, content, files, view, reply=False, **kwargs)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return await self.send_message(embed, content, files, view, reply=False, **kwargs)
        else:
            options = self._build_message_options(
                embed, content, None, view, **kwargs)
            edit_options = {k: v for k, v in options.items()
                            if k in ['embed', 'content', 'view', 'allowed_mentions', 'suppress_embeds']}
            try:
                await message.edit(**edit_options)
                return message
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                return await self.send_message(embed, content, files, view, reply=False, **kwargs)

    async def create_thread_if_needed(self, message: discord.Message, thread_name: str, auto_archive_duration: int = 1440, reason: str = None) -> Optional[discord.Thread]:
        """Create a thread from the message if conditions are met."""
        if isinstance(message.channel, discord.TextChannel):
            try:
                return await message.create_thread(
                    name=thread_name,
                    auto_archive_duration=auto_archive_duration,
                    reason=reason
                )
            except discord.HTTPException as e:
                logger.error(f"Failed to create thread: {e}")
                return None
        return None
