import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os

GUILD_ID = 1422970743595077797 #test

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


async def load_cogs():
    await bot.load_extension("cogs.welcome.welcome")
    await bot.load_extension("cogs.ticket.ticket")
    await bot.load_extension("cogs.support.support")
    await bot.load_extension("cogs.changelog.changelog")


@bot.event
async def on_ready():
    print(f"Bot started as {bot.user}")
    print("Guilds:", bot.guilds)

    guild = discord.Object(id=1422970743595077797)
    synced = await bot.tree.sync(guild=guild)

    print("SYNC RESULT:", synced)



async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


asyncio.run(main())
