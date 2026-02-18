import discord
from discord.ext import commands
from config import WELCOME_CHANNEL_ID


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(
            title="👋 Новий користувач",
            description=f"**{member}** приєднується до серверу!\n\n"
                        f"👥 Учасників на сервері: **{member.guild.member_count}**",
            color=0x0087E6
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
