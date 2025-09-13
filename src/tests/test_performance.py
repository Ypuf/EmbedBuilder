import pytest
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock
import discord
from embedbuilder.core import EmbedBuilder
from embedbuilder.utils import truncate_text, chunk_text
import inspect


class TestPerformance:
    @pytest.mark.slow
    def test_chunk_text_performance_large_input(self):
        print("Function source:")
        print(inspect.getsource(chunk_text))
        large_text = "Word " * (1024 * 100)

        start_time = time.time()
        chunks = chunk_text(large_text, max_chunk_size=4096, max_chunks=50)
        end_time = time.time()

        assert end_time - start_time < 5.0
        assert len(chunks) <= 50
        assert all(len(chunk) <= 4096 for chunk in chunks)

    @pytest.mark.slow
    def test_truncate_text_performance(self):
        very_long_text = "B" * (1024 * 1024)

        start_time = time.time()
        for _ in range(1000):
            result = truncate_text(very_long_text, 100)
        end_time = time.time()

        assert end_time - start_time < 2.0
        assert len(result) <= 100

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_many_embeds_creation_performance(self, mock_context):
        mock_messages = []
        for i in range(100):
            mock_message = MagicMock(spec=discord.Message)
            mock_messages.append(mock_message)

        mock_context.reply = AsyncMock(side_effect=mock_messages)

        start_time = time.time()

        for i in range(100):
            builder = EmbedBuilder(mock_context)
            builder.set_author("Test Author")
            builder.set_description(f"Test description {i}")

            messages = await builder.send()
            assert len(messages) == 1
            assert isinstance(messages[0], MagicMock)

        end_time = time.time()
        assert end_time - start_time < 3.0

    @pytest.mark.slow
    def test_many_fields_performance(self, mock_context):
        builder = EmbedBuilder(mock_context)

        start_time = time.time()

        for i in range(25):
            builder.add_field(f"Field {i}", f"Value {i}", i % 2 == 0)

        end_time = time.time()

        assert end_time - start_time < 1.0
        assert isinstance(builder, EmbedBuilder)

    @pytest.mark.slow
    def test_method_chaining_performance(self, mock_context):
        start_time = time.time()

        builder = (EmbedBuilder(mock_context)
                   .set_title("Title")
                   .set_description("Description")
                   .set_color(discord.Color.blue())
                   .set_url("https://example.com")
                   .set_author("Author", "https://example.com/icon.png")
                   .set_footer("Footer", "https://example.com/footer.png")
                   .set_thumbnail("https://example.com/thumb.png")
                   .set_image("https://example.com/image.png")
                   .add_field("F1", "V1", True)
                   .add_field("F2", "V2", False)
                   .add_field("F3", "V3", True)
                   .set_content("Content")
                   .set_reply(True)
                   .set_ephemeral(False)
                   .enable_pagination()
                   .set_timezone('UTC'))

        end_time = time.time()

        assert end_time - start_time < 0.1
        assert isinstance(builder, EmbedBuilder)


class TestMemoryUsage:
    @pytest.mark.slow
    def test_memory_usage_many_builders(self, mock_context):
        import gc

        gc.collect()
        initial_objects = len(gc.get_objects())

        builders = []
        for i in range(1000):
            builder = EmbedBuilder(mock_context)
            builder.set_title(f"Title {i}")
            builder.set_description(f"Description {i}")
            builders.append(builder)

        gc.collect()

        builders.clear()
        gc.collect()
        final_objects = len(gc.get_objects())

        assert final_objects - initial_objects < 100

    @pytest.mark.slow
    def test_large_embed_content_memory(self, mock_context):
        large_content = "X" * (1024 * 100)

        builder = EmbedBuilder(mock_context)
        builder.set_description(large_content)

        assert isinstance(builder, EmbedBuilder)


class TestConcurrency:

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_embed_building(self, mock_context):
        def create_mock_message(i):
            mock_message = MagicMock(spec=discord.Message)
            mock_embed = MagicMock(spec=discord.Embed)
            mock_embed.title = f"Title {i}"
            mock_embed.description = f"Description {i}"
            mock_message.embeds = [mock_embed]
            return mock_message

        mock_messages = [create_mock_message(i) for i in range(50)]
        mock_context.reply = AsyncMock(side_effect=mock_messages)

        async def build_embed(i):
            builder = EmbedBuilder(mock_context)
            builder.set_author(f"Author {i}")
            builder.set_title(f"Title {i}")
            builder.set_description(f"Description {i}")
            messages = await builder.send()
            return messages[0]

        tasks = [build_embed(i) for i in range(50)]
        start_time = time.time()
        messages = await asyncio.gather(*tasks)
        end_time = time.time()

        assert len(messages) == 50
        assert end_time - start_time < 5.0

        for i, message in enumerate(messages):
            assert len(message.embeds) == 1
            embed = message.embeds[0]
            assert embed.title == f"Title {i}"
            assert embed.description == f"Description {i}"


class TestEdgeCasePerformance:
    @pytest.mark.slow
    def test_empty_string_operations(self, mock_context):
        builder = EmbedBuilder(mock_context)

        start_time = time.time()

        for _ in range(10000):
            builder.set_title("")
            builder.set_description("")
            builder.set_url("")
            builder.set_content("")

        end_time = time.time()
        assert end_time - start_time < 2.0

    @pytest.mark.slow
    def test_unicode_text_performance(self, mock_context):
        unicode_text = "testðŸŽ‰testðŸš€" * 50

        start_time = time.time()
        chunks = chunk_text(unicode_text, max_chunk_size=1000)
        end_time = time.time()

        assert end_time - start_time < 1.0
        assert len(chunks) >= 1

    @pytest.mark.slow
    def test_nested_markdown_performance(self, mock_context):
        markdown_text = """
        # Header
        **Bold** and *italic*
        `code`
        > Quote
        - List item
        """ * 100

        start_time = time.time()
        chunks = chunk_text(markdown_text, max_chunk_size=2000)
        end_time = time.time()

        assert end_time - start_time < 2.0
        assert len(chunks) >= 1


class TestStressTests:
    @pytest.mark.slow
    def test_maximum_fields_stress(self, mock_context):
        builder = EmbedBuilder(mock_context)

        fields = [(f"Field {i}", f"Value {i}", i % 2 == 0) for i in range(25)]

        start_time = time.time()
        builder.add_fields(fields)
        end_time = time.time()

        assert end_time - start_time < 0.5
        assert isinstance(builder, EmbedBuilder)

    @pytest.mark.slow
    def test_maximum_description_length_stress(self, mock_context):
        max_description = "A" * 4096

        builder = EmbedBuilder(mock_context)

        start_time = time.time()
        builder.set_description(max_description)
        end_time = time.time()

        assert end_time - start_time < 0.1
        assert isinstance(builder, EmbedBuilder)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_rapid_method_calls(self, mock_context):
        builder = EmbedBuilder(mock_context)
        builder.set_author("Test Author")

        start_time = time.time()

        for i in range(1000):
            (builder
             .set_title(f"Title {i}")
             .set_description(f"Desc {i}")
             .set_color(discord.Color.blue()))

        end_time = time.time()

        assert end_time - start_time < 1.0
        assert isinstance(builder, EmbedBuilder)


pytestmark = pytest.mark.slow


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
