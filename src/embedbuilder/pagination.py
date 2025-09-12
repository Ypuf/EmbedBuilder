import discord
from typing import List


class PaginationView(discord.ui.View):

    def __init__(self, embeds: List[discord.Embed], timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.total_pages = len(embeds)

        if self.total_pages > 1:
            if self.total_pages > 3:
                self.add_item(self._create_button(
                    "⏮️", self.first_page_callback, discord.ButtonStyle.blurple))
                self.add_item(self._create_button(
                    "◀️", self.prev_page_callback, discord.ButtonStyle.secondary))
                self.add_item(self._create_button(
                    "▶️", self.next_page_callback, discord.ButtonStyle.secondary))
                self.add_item(self._create_button(
                    "⏭️", self.last_page_callback, discord.ButtonStyle.blurple))
            else:
                self.add_item(self._create_button(
                    "◀️", self.prev_page_callback, discord.ButtonStyle.secondary))
                self.add_item(self._create_button(
                    "▶️", self.next_page_callback, discord.ButtonStyle.secondary))

    def _create_button(self, emoji: str, callback, style: discord.ButtonStyle) -> discord.ui.Button:
        button = discord.ui.Button(emoji=emoji, style=style)
        button.callback = callback
        return button

    async def update_buttons(self, interaction: discord.Interaction):
        embed = self.embeds[self.current_page]

        for child in self.children:
            if isinstance(child, discord.ui.Button):
                emoji = child.emoji.name if child.emoji else ""
                if emoji == "⏮️" or emoji == "◀️":
                    child.disabled = self.current_page == 0
                elif emoji == "▶️" or emoji == "⏭️":
                    child.disabled = self.current_page == self.total_pages - 1

        await interaction.response.edit_message(embed=embed, view=self)

    async def first_page_callback(self, interaction: discord.Interaction):
        self.current_page = 0
        await self.update_buttons(interaction)

    async def prev_page_callback(self, interaction: discord.Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_buttons(interaction)

    async def next_page_callback(self, interaction: discord.Interaction):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_buttons(interaction)

    async def last_page_callback(self, interaction: discord.Interaction):
        self.current_page = self.total_pages - 1
        await self.update_buttons(interaction)

    @property
    def current_embed(self) -> discord.Embed:
        return self.embeds[self.current_page]

    def add_page(self, embed: discord.Embed):
        self.embeds.append(embed)
        self.total_pages = len(self.embeds)

    def remove_page(self, index: int):
        if 0 <= index < self.total_pages:
            self.embeds.pop(index)
            self.total_pages = len(self.embeds)
            if self.current_page >= self.total_pages:
                self.current_page = max(0, self.total_pages - 1)
