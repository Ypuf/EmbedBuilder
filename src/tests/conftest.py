import pytest
import asyncio
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
import discord
from discord.ext import commands


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_bot():
    bot = MagicMock(spec=commands.Bot)
    bot.user = MagicMock(spec=discord.ClientUser)
    bot.user.id = 98765
    bot.user.name = "TestBot"
    return bot


@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)
    guild.id = 67890
    guild.name = "Test Guild"
    guild.icon = None
    return guild


@pytest.fixture
def mock_user():
    user = MagicMock(spec=discord.User)
    user.id = 12077
    user.name = "TestUser"
    user.display_name = "Test User"
    user.avatar = None
    user.create_dm = AsyncMock()
    return user


@pytest.fixture
def mock_member(mock_guild, mock_user):
    member = MagicMock(spec=discord.Member)
    member.id = mock_user.id
    member.name = mock_user.name
    member.display_name = "Test Member"
    member.guild = mock_guild
    member.avatar = None
    return member


@pytest.fixture
def mock_channel():
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 11111
    channel.name = "test-channel"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_dm_channel():
    channel = MagicMock(spec=discord.DMChannel)
    channel.id = 22222
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_thread():
    thread = MagicMock(spec=discord.Thread)
    thread.id = 33333
    thread.name = "test-thread"
    thread.send = AsyncMock()
    return thread


@pytest.fixture
def mock_forum_channel():
    channel = MagicMock(spec=discord.ForumChannel)
    channel.id = 44444
    channel.name = "test-forum"
    channel.create_thread = AsyncMock()
    return channel


@pytest.fixture
def mock_context(mock_bot, mock_member, mock_channel, mock_guild):
    ctx = MagicMock(spec=commands.Context)
    ctx.bot = mock_bot
    ctx.author = mock_member
    ctx.channel = mock_channel
    ctx.guild = mock_guild
    ctx.message = MagicMock(spec=discord.Message)
    ctx.message.id = 55555
    ctx.reply = AsyncMock()
    ctx.send = AsyncMock()
    return ctx


@pytest.fixture
def mock_interaction(mock_member, mock_channel, mock_guild):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = mock_member
    interaction.channel = mock_channel
    interaction.guild = mock_guild
    interaction.response = MagicMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.response.send_message = AsyncMock()
    interaction.original_response = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    interaction.client = MagicMock()
    return interaction


@pytest.fixture
def mock_message(mock_member, mock_channel):
    message = MagicMock(spec=discord.Message)
    message.id = 66666
    message.author = mock_member
    message.channel = mock_channel
    message.content = "Test message"
    message.edit = AsyncMock()
    message.delete = AsyncMock()
    message.create_thread = AsyncMock()
    return message


@pytest.fixture
def sample_embed():
    embed = discord.Embed(
        title="Test Embed",
        description="This is a test embed",
        color=discord.Color.blue()
    )
    embed.add_field(name="Field 1", value="Value 1", inline=True)
    embed.add_field(name="Field 2", value="Value 2", inline=False)
    embed.set_footer(text="Test Footer")
    return embed


@pytest.fixture
def temp_image_file():
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde')
        temp_path = f.name

    yield temp_path

    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def temp_text_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is test content\nLine 2\nLine 3")
        temp_path = f.name

    yield temp_path

    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def long_text():
    return "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100


@pytest.fixture
def very_long_text():
    return "A" * 10000


@pytest.fixture
def mock_discord_file():
    file = MagicMock(spec=discord.File)
    file.filename = "test.png"
    return file


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "discord: mark test as Discord API related")


def assert_embed_equal(embed1, embed2):
    assert embed1.title == embed2.title
    assert embed1.description == embed2.description
    assert embed1.color == embed2.color
    assert embed1.url == embed2.url
    assert len(embed1.fields) == len(embed2.fields)

    for field1, field2 in zip(embed1.fields, embed2.fields):
        assert field1.name == field2.name
        assert field1.value == field2.value
        assert field1.inline == field2.inline


def create_mock_async_context_manager():
    class MockAsyncContextManager:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockAsyncContextManager()


@pytest.fixture
def async_return():
    def _async_return(value):
        async def _():
            return value
        return _()
    return _async_return


@pytest.fixture
def async_raise():
    def _async_raise(exception):
        async def _():
            raise exception
        return _()
    return _async_raise
