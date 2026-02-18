import discord
from discord.ext import commands
from config import ADMIN_ROLE_ID, SUPPORT_ROLE_IDS


class CloseSupportView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Моя проблема вирішена",
        style=discord.ButtonStyle.success,
        custom_id="support_ticket_resolved"
    )
    async def resolve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.channel, discord.Thread):
            return

        await interaction.response.send_message("Звернення зачинено.")
        await interaction.channel.edit(archived=True, locked=True)


class SupportView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Створити звернення",
        style=discord.ButtonStyle.primary,
        custom_id="support_create_ticket"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "Це можна використовувати тільки в текстовому каналі.",
                ephemeral=True
            )
            return

        thread = await channel.create_thread(
            name=f"Звернення - {interaction.user}",
            auto_archive_duration=1440
        )

        await thread.add_user(interaction.user)

        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

        support_roles = [
            interaction.guild.get_role(rid) for rid in SUPPORT_ROLE_IDS
        ]
        support_roles = [r for r in support_roles if r]

        if admin_role:
            for member in admin_role.members:
                await thread.add_user(member)

            for role in support_roles:
                for member in role.members:
                    await thread.add_user(member)

        mentions = " ".join(r.mention for r in support_roles)


        await thread.send(
            content=(
                f"{mentions}\n"
                f"Привіт, {interaction.user.mention}!\n"
                "Це ваша особиста гілка звернення.\n"
                "Опишіть, будь ласка, вашу проблему."
            ),
            view=CloseSupportView()
        )

        await interaction.response.send_message(
            f"Тікет створено: {thread.mention}",
            ephemeral=True
        )


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(SupportView(bot))
        bot.add_view(CloseSupportView())

    @commands.command(name="supportpanel")
    @commands.has_permissions(administrator=True)
    async def supportpanel(self, ctx):
        try:
            await ctx.message.delete()
        except Exception as e:
            print("Delete error:", e)

        embed = discord.Embed(
            title="Технічна підтримка",
            description="Натисніть кнопку нижче, щоб створити звернення.",
            color=0x3498db
        )

        await ctx.send(embed=embed, view=SupportView(self.bot))


async def setup(bot):
    await bot.add_cog(Support(bot))
