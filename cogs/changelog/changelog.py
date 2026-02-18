import asyncio
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import ADMIN_ROLE_ID, TARGET_CHANNEL_ID

GUILD_ID = 1422970743595077797


def admin_only():
    async def predicate(interaction: discord.Interaction):
        return any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles)
    return app_commands.check(predicate)


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = []

        group = app_commands.Group(name="changelog", description="Changelog tools")

        @group.command(name="sendnow")
        @admin_only()
        async def sendnow(interaction: discord.Interaction, link: str):
            await interaction.response.defer(ephemeral=True)
            await self.send_message_from_link(link)
            await interaction.followup.send("done", ephemeral=True)

        @group.command(name="schedule")
        @admin_only()
        async def schedule(interaction: discord.Interaction, time: str, link: str):
            await interaction.response.defer(ephemeral=True)

            when = datetime.strptime(time, "%Y-%m-%d %H:%M")
            task = self.bot.loop.create_task(self.schedule_worker(when, link))
            self.tasks.append((when, link, task))

            await interaction.followup.send("scheduled", ephemeral=True)

        @group.command(name="list")
        @admin_only()
        async def list_cmd(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            if not self.tasks:
                await interaction.followup.send("empty", ephemeral=True)
                return

            text = "\n".join(
                f"{i+1}. {t[0].strftime('%Y-%m-%d %H:%M')}"
                for i, t in enumerate(self.tasks)
            )

            await interaction.followup.send(text, ephemeral=True)

        @group.command(name="clear")
        @admin_only()
        async def clear(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            for _, _, task in self.tasks:
                task.cancel()

            self.tasks.clear()
            await interaction.followup.send("cleared", ephemeral=True)

        bot.tree.add_command(group, guild=discord.Object(id=GUILD_ID))

    async def send_message_from_link(self, link: str):
        parts = link.split("/")
        channel_id = int(parts[-2])
        message_id = int(parts[-1])

        channel = await self.bot.fetch_channel(channel_id)
        msg = await channel.fetch_message(message_id)

        target = await self.bot.fetch_channel(TARGET_CHANNEL_ID)

        files = [await att.to_file() for att in msg.attachments]

        await target.send(
            content=msg.content,
            embeds=msg.embeds,
            files=files
        )

    async def schedule_worker(self, when: datetime, link: str):
        delay = (when - datetime.now()).total_seconds()
        if delay > 0:
            await asyncio.sleep(delay)
        await self.send_message_from_link(link)


async def setup(bot):
    await bot.add_cog(Scheduler(bot))
