import json
import aiohttp
import discord
from discord.ext import commands, tasks
from typing import Dict

from config import ADMIN_API_URL, ADMINS_CHANNEL_ID, ADMIN_ALLOWED_ROLE_IDS, ADMIN_MAPPINGS_FILE, SERVER_NAME

def load_mappings() -> Dict[str, int]:
    try:
        with open(ADMIN_MAPPINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_mappings(data: Dict[str, int]):
    with open(ADMIN_MAPPINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def fetch_data(api_url: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as response:
                if response.status != 200:
                    return None
                return await response.json()
    except Exception:
        return None

class Admins(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.update_admins_loop.start()

    def cog_unload(self):
        self.update_admins_loop.cancel()

    @commands.command(name="addadmintobot")
    async def add_admin_command(self, ctx: commands.Context):
        """
        Usage: !addadmintobot @user uuid
        """
        if ctx.author.bot:
            return

        allowed = any(r.id in ADMIN_ALLOWED_ROLE_IDS for r in ctx.author.roles)
        if not allowed:
            await ctx.send("❌ У вас немає прав.")
            return

        parts = ctx.message.content.split()
        if len(parts) < 3 or not ctx.message.mentions:
            await ctx.send("Формат: !addadmintobot @user uuid")
            return

        user = ctx.message.mentions[0]
        try:
            uuid = int(parts[-1])
        except Exception:
            await ctx.send("UUID має бути числом.")
            return

        data = load_mappings()
        if "uuid_to_discord" not in data:
            data["uuid_to_discord"] = {}

        data["uuid_to_discord"][str(uuid)] = user.id
        save_mappings(data)

        await ctx.send(f"uuid {uuid} прив'язано до {user.mention}")

    @tasks.loop(minutes=1)
    async def update_admins_loop(self):
        channel = self.bot.get_channel(ADMINS_CHANNEL_ID)
        if not channel:
            return

        data = await fetch_data(ADMIN_API_URL)
        if not data:
            return

        admins = data.get("admins", [])
        params = data.get("params", {})

        server_online = params.get("players", 0)
        server_peak = params.get("peak", 0)

        embed = discord.Embed(
            title=f"💎 {SERVER_NAME}({server_online})",
            color=discord.Color.blurple()
        )

        if not admins:
            embed.description = "Адміністраторів онлайн немає."
            embed.set_footer(text=f"Піковий онлайн: {server_peak}")
            await channel.send(embed=embed)
            return

        mappings = load_mappings().get("uuid_to_discord", {})
        guild = channel.guild

        lines = []
        for admin in sorted(admins, key=lambda x: x.get("level", 0), reverse=True):
            nickname = admin.get("name", "Unknown")
            level = admin.get("level", 0)
            uuid = str(admin.get("uuid"))

            if uuid not in mappings:
                status_part = "❓"
            else:
                discord_id = mappings[uuid]
                member = guild.get_member(int(discord_id)) if guild else None

                if member and member.voice and member.voice.channel:
                    if member.is_on_mobile():
                        status_part = "✅📱"
                    else:
                        status_part = "✅🖥️"
                else:
                    status_part = "❌"

            line = f"{status_part} Нік: **{nickname}** Рівень: {level}"
            lines.append(line)

        description = f"**Адмінів в мережі: {len(admins)}**\n"
        description += "━━━━━━━━━━━━━━━━━━\n"
        description += "\n".join(lines)

        players_per_admin = round(server_online / len(admins)) if admins else 0
        description += f"\n\nНа 1 адміна приходиться {players_per_admin} гравців."

        embed.description = description
        embed.set_footer(text=f"Піковий онлайн: {server_peak}")

        await channel.send(embed=embed)

    @update_admins_loop.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Admins(bot))