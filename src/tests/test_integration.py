import pytest
import discord
from unittest.mock import AsyncMock, MagicMock
from discord.ext import commands

from embedbuilder.core import EmbedBuilder


class TestIntegration:
    @pytest.mark.asyncio
    async def test_full_embed_workflow(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.reply = AsyncMock()

        mock_message = MagicMock(spec=discord.Message)
        ctx.reply.return_value = mock_message

        builder = EmbedBuilder(ctx)

        messages = await (builder
                          .set_author("Test Author")
                          .set_title("Integration Test")
                          .set_description("This is a test embed")
                          .set_color(discord.Color.green())
                          .add_field("Field 1", "Value 1", True)
                          .add_field("Field 2", "Value 2", False)
                          .set_footer("Test Footer")
                          .send())

        assert len(messages) == 1
        ctx.reply.assert_called_once()

        call_args = ctx.reply.call_args
        assert 'embed' in call_args.kwargs

    @pytest.mark.asyncio
    async def test_forum_channel_workflow(self):
        forum_channel = MagicMock(spec=discord.ForumChannel)
        mock_thread = MagicMock(spec=discord.Thread)
        forum_channel.create_thread = AsyncMock(return_value=mock_thread)

        mock_message = MagicMock(spec=discord.Message)
        mock_thread.send = AsyncMock(return_value=mock_message)

        builder = EmbedBuilder(forum_channel)

        messages = await (builder
                          .set_author("Test Author")
                          .create_forum_thread("Test Thread")
                          .set_title("Forum Test")
                          .set_description("Forum thread content")
                          .send())

        forum_channel.create_thread.assert_called_once()
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_complete_workflow_with_all_features(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.reply = AsyncMock()

        mock_message = MagicMock(spec=discord.Message)
        ctx.reply.return_value = mock_message

        builder = EmbedBuilder(ctx)

        messages = await (builder
                          .set_author("Bot Name", "https://example.com/icon.png")
                          .set_title("Complete Test Embed")
                          .set_description("This tests multiple features at once")
                          .set_color(discord.Color.blue())
                          .set_url("https://example.com")
                          .set_thumbnail("https://example.com/thumb.png")
                          .set_image("https://example.com/image.png")
                          .add_field("Field 1", "Value 1", True)
                          .add_field("Field 2", "Value 2", True)
                          .add_field("Field 3", "Value 3", False)
                          .set_footer("Footer text", "https://example.com/footer.png")
                          .set_content("Message content above embed")
                          .set_timestamp()
                          .send())

        assert len(messages) == 1
        ctx.reply.assert_called_once()

        call_args = ctx.reply.call_args
        assert 'embed' in call_args.kwargs
        assert 'content' in call_args.kwargs

    @pytest.mark.asyncio
    async def test_interaction_workflow(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.id = 67890
        interaction.channel = MagicMock(spec=discord.TextChannel)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.send_message = AsyncMock()
        interaction.original_response = AsyncMock()

        mock_bot = MagicMock()
        mock_bot.get_embed_colour.return_value = 0x7289DA
        interaction.client = mock_bot

        mock_message = MagicMock(spec=discord.Message)
        interaction.original_response.return_value = mock_message

        builder = EmbedBuilder(interaction)

        messages = await (builder
                          .set_author("Slash Command Bot")
                          .set_title("Slash Command Response")
                          .set_description("This is a slash command response")
                          .set_ephemeral(True)
                          .send())

        assert len(messages) == 1
        interaction.response.send_message.assert_called_once()

        call_args = interaction.response.send_message.call_args
        assert call_args.kwargs.get('ephemeral') == True

    @pytest.mark.asyncio
    async def test_thread_creation_workflow(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.reply = AsyncMock()

        mock_message = MagicMock(spec=discord.Message)
        mock_thread = MagicMock(spec=discord.Thread)
        mock_message.create_thread = AsyncMock(return_value=mock_thread)
        ctx.reply.return_value = mock_message

        builder = EmbedBuilder(ctx)

        messages = await (builder
                          .set_author("Thread Creator")
                          .set_title("Thread Starter Message")
                          .set_description("This message will start a thread")
                          .create_thread("Discussion Thread",
                                         auto_archive_duration=1440,
                                         reason="Starting discussion")
                          .send())

        assert len(messages) == 1
        ctx.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.reply = AsyncMock()

        builder = EmbedBuilder(ctx)

        with pytest.raises(ValueError):
            await (builder
                   .set_title("A" * 300)
                   .set_author("Valid Author")
                   .send())

        builder2 = EmbedBuilder(ctx)
        with pytest.raises(ValueError):
            await (builder2
                   .set_author("Valid Author")
                   .set_file_path("/nonexistent/file.png")
                   .send())
