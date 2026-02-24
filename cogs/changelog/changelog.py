import asyncio
from datetime import datetime
import discord
from discord.ext import commands
from config import ADMIN_ROLE_ID, TARGET_CHANNEL_ID

GUILD_ID = 1422970743595077797


def admin_only():
    async def predicate(ctx: commands.Context):
        return any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)


class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = []

    @commands.command(name="sendnow")
    @admin_only()
    async def sendnow(self, ctx: commands.Context, link: str):
        await self.send_message_from_link(link)
        await ctx.send("done")

    @commands.command(name="schedule")
    @admin_only()
    async def schedule(self, ctx: commands.Context, time: str, *, link: str):
        try:
            when = datetime.strptime(time, "%Y-%m-%d %H:%M")
        except ValueError:
            await ctx.send("Format: YYYY-MM-DD HH:MM")
            return

        task = self.bot.loop.create_task(self.schedule_worker(when, link))
        self.tasks.append((when, link, task))

        await ctx.send("scheduled")

    @commands.command(name="list")
    @admin_only()
    async def list_tasks(self, ctx: commands.Context):
        if not self.tasks:
            await ctx.send("empty")
            return

        text = "\n".join(
            f"{i+1}. {t[0].strftime('%Y-%m-%d %H:%M')}"
            for i, t in enumerate(self.tasks)
        )

        await ctx.send(text)

    @commands.command(name="clear")
    @admin_only()
    async def clear(self, ctx: commands.Context):
        for _, _, task in self.tasks:
            task.cancel()

        self.tasks.clear()
        await ctx.send("cleared")

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