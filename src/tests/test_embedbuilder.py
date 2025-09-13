import pytest
import discord
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands

from embedbuilder.core import EmbedBuilder
from embedbuilder.customization import EmbedCustomizer
from embedbuilder.pagination import PaginationView
from embedbuilder.utils import truncate_text, chunk_text


class TestUtils:
    def test_truncate_text_normal(self):
        text = "This is a long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert result == "This is a long te..."
        assert len(result) <= 20

    def test_truncate_text_short(self):
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == "Short text"

    def test_truncate_text_empty(self):
        result = truncate_text("", 20)
        assert result == ""

    def test_truncate_text_custom_suffix(self):
        text = "This is a long text"
        result = truncate_text(text, 15, suffix="...")
        assert result.endswith("...")
        assert len(result) <= 15

    def test_chunk_text_simple(self):
        text = "A B C D E " * 1000
        chunks = chunk_text(text, max_chunk_size=1000)
        assert len(chunks) <= 10
        assert all(len(chunk) <= 1000 for chunk in chunks)

    def test_chunk_text_by_paragraphs(self):
        text = "Para1\n\nPara2\n\nPara3"
        chunks = chunk_text(text, max_chunk_size=50)
        assert len(chunks) >= 1

    def test_chunk_text_empty_raises_error(self):
        with pytest.raises(ValueError, match="Description cannot be empty"):
            chunk_text("")

    def test_chunk_text_max_chunks_limit(self):
        text = "ABC\n\nDEF\n\nGHI\n\nJKL\n\nMNO"
        chunks = chunk_text(text, max_chunk_size=5, max_chunks=3)
        assert len(chunks) <= 3


class TestEmbedCustomizer:
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.bot = None
        return ctx

    @pytest.fixture
    def mock_interaction(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.user.color = discord.Colour.default()
        interaction.user.display_avatar = MagicMock()
        interaction.user.display_avatar.url = "https://example.com/avatar.png"
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.id = 67890
        interaction.guild.me = MagicMock(spec=discord.Member)
        interaction.channel = MagicMock(spec=discord.TextChannel)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.send_message = AsyncMock()
        interaction.original_response = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        interaction.client = MagicMock()
        interaction.client.get_embed_colour = MagicMock(
            return_value=discord.Colour.blue())
        return interaction

    def test_customizer_with_context(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        assert customizer.user == mock_context.author
        assert customizer.guild == mock_context.guild

    def test_customizer_with_interaction(self, mock_interaction):
        customizer = EmbedCustomizer(mock_interaction)
        assert customizer.user == mock_interaction.user
        assert customizer.guild == mock_interaction.guild

    def test_get_embed_colour_default(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        color = customizer.get_embed_colour()
        assert color == 0x7289DA

    def test_get_embed_colour_provided(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        custom_color = discord.Color.red()
        color = customizer.get_embed_colour(custom_color)
        assert color == custom_color

    def test_get_author_name_default(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        name = customizer.get_author_name()
        assert name == ""

    def test_get_author_name_custom(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        custom_name = "Custom Author"
        name = customizer.get_author_name(custom_name)
        assert name == custom_name

    def test_get_all_custom_values(self, mock_context):
        customizer = EmbedCustomizer(mock_context)
        values = customizer.get_all_custom_values()
        assert len(values) == 5
        assert values[0] == 0x7289DA
        assert values[1] == ""


class TestPaginationView:
    @pytest.fixture
    def sample_embeds(self):
        embeds = []
        for i in range(3):
            embed = discord.Embed(
                title=f"Page {i+1}", description=f"Content {i+1}")
            embeds.append(embed)
        return embeds

    @pytest.mark.asyncio
    async def test_pagination_view_creation(self, sample_embeds):
        view = PaginationView(sample_embeds)
        assert view.total_pages == 3
        assert view.current_page == 0
        assert len(view.children) > 0

    @pytest.mark.asyncio
    async def test_pagination_view_single_page(self):
        embed = discord.Embed(title="Single Page")
        view = PaginationView([embed])
        assert view.total_pages == 1
        assert len(view.children) == 0

    @pytest.mark.asyncio
    async def test_current_embed_property(self, sample_embeds):
        view = PaginationView(sample_embeds)
        assert view.current_embed == sample_embeds[0]
        view.current_page = 1
        assert view.current_embed == sample_embeds[1]

    @pytest.mark.asyncio
    async def test_add_page(self, sample_embeds):
        view = PaginationView(sample_embeds)
        new_embed = discord.Embed(title="New Page")
        view.add_page(new_embed)
        assert view.total_pages == 4
        assert view.embeds[-1] == new_embed

    @pytest.mark.asyncio
    async def test_remove_page(self, sample_embeds):
        view = PaginationView(sample_embeds)
        view.remove_page(1)
        assert view.total_pages == 2
        assert view.embeds[1].title == "Page 3"

    @pytest.mark.asyncio
    async def test_navigation_callbacks(self, sample_embeds):
        view = PaginationView(sample_embeds)
        mock_interaction = AsyncMock(spec=discord.Interaction)
        mock_interaction.response.edit_message = AsyncMock()

        await view.next_page_callback(mock_interaction)
        assert view.current_page == 1

        await view.last_page_callback(mock_interaction)
        assert view.current_page == 2

        await view.prev_page_callback(mock_interaction)
        assert view.current_page == 1

        await view.first_page_callback(mock_interaction)
        assert view.current_page == 0


class TestEmbedBuilder:
    @pytest.fixture
    def mock_context(self):
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock(spec=discord.Member)
        ctx.author.id = 12345
        ctx.guild = MagicMock(spec=discord.Guild)
        ctx.guild.id = 67890
        ctx.channel = MagicMock(spec=discord.TextChannel)
        ctx.reply = AsyncMock()
        ctx.send = AsyncMock()
        return ctx

    @pytest.fixture
    def mock_interaction(self):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.Member)
        interaction.user.id = 12345
        interaction.user.color = discord.Colour.default()
        interaction.user.display_avatar = MagicMock()
        interaction.user.display_avatar.url = "https://example.com/avatar.png"
        interaction.guild = MagicMock(spec=discord.Guild)
        interaction.guild.id = 67890
        interaction.guild.me = MagicMock(spec=discord.Member)
        interaction.channel = MagicMock(spec=discord.TextChannel)
        interaction.response = MagicMock()
        interaction.response.is_done.return_value = False
        interaction.response.send_message = AsyncMock()
        interaction.original_response = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        interaction.client = MagicMock()
        interaction.client.get_embed_colour = MagicMock(
            return_value=discord.Colour.blue())
        return interaction

    def test_embedbuilder_initialization(self, mock_context):
        builder = EmbedBuilder(mock_context)
        assert builder.source == mock_context
        assert hasattr(builder, 'customizer')
        assert builder._reply == True

    def test_method_chaining(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = (builder
                  .set_title("Test Title")
                  .set_description("Test Description")
                  .set_color(discord.Color.blue()))

        assert result is builder

    def test_aliases(self, mock_context):
        builder = EmbedBuilder(mock_context)

        result = (builder
                  .title("Test")
                  .desc("Description")
                  .color(discord.Color.red()))

        assert result is builder

    def test_add_field(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = builder.add_field("Field 1", "Value 1", True)
        assert result is builder

    def test_add_fields_bulk(self, mock_context):
        builder = EmbedBuilder(mock_context)
        fields = [
            ("Field 1", "Value 1", True),
            ("Field 2", "Value 2", False),
            ("Field 3", "Value 3")
        ]
        result = builder.add_fields(fields)
        assert result is builder

    def test_add_fields_invalid_tuple(self, mock_context):
        builder = EmbedBuilder(mock_context)
        with pytest.raises(ValueError, match="Field tuple must have 2 or 3 elements"):
            builder.add_fields([("Field 1",)])

    @pytest.mark.asyncio
    async def test_embedbuilder_debug(self, mock_context):
        builder = EmbedBuilder(mock_context)

        print(f"Builder type: {type(builder)}")
        print(f"Builder __dict__: {builder.__dict__}")

        try:
            title = getattr(builder, '_title', 'NOT_FOUND')
            print(f"_title value: {title}")
        except Exception as e:
            print(f"Error accessing _title: {e}")

        builder.set_title("Test Title")
        try:
            title = getattr(builder, '_title', 'NOT_FOUND')
            print(f"_title after set_title: {title}")
        except Exception as e:
            print(f"Error accessing _title after set_title: {e}")

    @pytest.mark.asyncio
    async def test_build_embed_basic(self, mock_context):
        builder = EmbedBuilder(mock_context).set_title("Test Title").set_description(
            "Test Description").set_author("Test Author")

        assert builder._title == "Test Title"
        assert builder._description == "Test Description"
        assert builder._author_name == "Test Author"

        messages = await builder.send()
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_build_embed_with_fields(self, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_title("Test").add_field(
            "Field", "Value", True).set_author("Test")

        assert builder._title == "Test"
        assert builder._author_name == "Test"
        assert len(builder._fields) == 1
        assert builder._fields[0] == ("Field", "Value", True)

        messages = await builder.send()
        assert len(messages) == 1

    def test_pagination_setup(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = builder.enable_pagination(timeout=300.0)
        assert result is builder

    def test_add_page(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = builder.add_page(title="Page 1", description="Content 1")
        assert result is builder

    def test_file_handling(self, mock_context):
        builder = EmbedBuilder(mock_context)

        result1 = builder.set_file_path("/path/to/file.png")
        assert result1 is builder

        mock_file = MagicMock(spec=discord.File)
        result2 = builder.add_file(mock_file)
        assert result2 is builder

    def test_thread_creation_setup(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = builder.create_thread(
            "Test Thread", auto_archive_duration=60, reason="Testing")
        assert result is builder

    def test_forum_thread_setup(self, mock_context):
        builder = EmbedBuilder(mock_context)
        result = builder.create_forum_thread("Forum Thread", "Content")
        assert result is builder

    @pytest.mark.asyncio
    async def test_send_validation_errors(self, mock_context):
        builder = EmbedBuilder(mock_context)

        builder.set_author("Valid Author")
        builder.set_title("A" * 300)
        with pytest.raises(ValueError):
            await builder.send()

    @pytest.mark.asyncio
    async def test_send_file_not_found(self, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_author("Valid Author")
        builder.set_file_path("/nonexistent/file.png")

        with pytest.raises(ValueError):
            await builder.send()

    @pytest.mark.asyncio
    @patch('os.path.exists', return_value=True)
    async def test_send_single_embed_context(self, mock_exists, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_author("Test Author")
        builder.set_title("Test").set_description("Short description")

        mock_message = MagicMock(spec=discord.Message)
        mock_context.reply.return_value = mock_message

        messages = await builder.send()

        assert len(messages) == 1
        assert messages[0] == mock_message
        mock_context.reply.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_single_embed_interaction(self, mock_interaction):
        builder = EmbedBuilder(mock_interaction)
        builder.set_author("Test Author")
        builder.set_title("Test").set_description("Short description")

        mock_message = MagicMock(spec=discord.Message)
        mock_interaction.original_response.return_value = mock_message

        messages = await builder.send()

        assert len(messages) == 1
        mock_interaction.response.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_multiple_embeds(self, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_author("Test Author")
        builder.set_title("Test").set_description(
            "A" * 5000)

        mock_messages = [MagicMock(spec=discord.Message) for _ in range(2)]
        mock_context.reply.return_value = mock_messages[0]
        mock_context.channel.send.return_value = mock_messages[1]

        with patch('embedbuilder.core.chunk_text') as mock_chunk:
            mock_chunk.return_value = ["Chunk 1", "Chunk 2"]

            messages = await builder.send()

            assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_send_paginated(self, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_author("Test Author")
        builder.enable_pagination()
        builder.add_page("Page 1", "Content 1")
        builder.add_page("Page 2", "Content 2")

        mock_message = MagicMock(spec=discord.Message)
        mock_context.reply.return_value = mock_message

        with patch('embedbuilder.pagination.PaginationView') as mock_pagination:
            mock_view = MagicMock()
            mock_pagination.return_value = mock_view

            messages = await builder.send()

            assert len(messages) == 1
            mock_context.reply.assert_called_once()

    def test_edit_message_setup(self, mock_context):
        mock_message = MagicMock(spec=discord.Message)
        builder = EmbedBuilder(mock_context)

        result = builder.edit_message(mock_message)
        assert result is builder

    def test_ephemeral_setup(self, mock_context):
        builder = EmbedBuilder(mock_context)

        result = builder.set_ephemeral(True)
        assert result is builder

        result2 = builder.set_ephemeral(False)
        assert result2 is builder

    def test_delete_after_setup(self, mock_context):
        builder = EmbedBuilder(mock_context)

        result = builder.set_delete_after(30.0)
        assert result is builder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
