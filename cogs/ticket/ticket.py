import discord
from discord.ext import commands
from config import TICKET_CHANNEL_ID, ADMIN_ROLE_ID


FIRST_MESSAGE = """
Будь ласка, уважно заповніть форму звернення:

• 🔧 Вкажіть наявність модифікацій/редуксів.
• ⏳ Опишіть, як давно було виявлено баг.
• 📎 Додайте докази у вигляді відео або скріншоту.

⚠️ Репорти без доказів будуть відхилені.
"""


class TicketModal(discord.ui.Modal, title="Створення звернення"):
    description = discord.ui.TextInput(
        label="Опишіть проблему",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=400
    )

    steps = discord.ui.TextInput(
        label="Як відтворити",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=400
    )

    proof = discord.ui.TextInput(
        label="Докази (посилання чи опис)",
        style=discord.TextStyle.short,
        required=True,
        max_length=400
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Дякуємо за звернення!",
            ephemeral=True
        )

        channel = interaction.client.get_channel(TICKET_CHANNEL_ID)
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)

        embed = discord.Embed(
            title="Нове звернення",
            description=(
                f"📝 **Опис**\n{self.description.value}\n\n"
                f"📋 **Як відтворити**\n{self.steps.value}\n\n"
                f"📎 **Докази**\n{self.proof.value}"
            ),
            color=0x0087E6
        )

        embed.set_footer(text=f"ID користувача: {interaction.user.id}")

        mention = admin_role.mention if admin_role else ""

        await channel.send(
            content=f"{mention} 📨 Нове звернення від {interaction.user.mention}",
            embed=embed
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Створити звернення",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_create"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketView())

    @commands.command()
    async def ticketpanel(self, ctx):
        if not ctx.author.get_role(ADMIN_ROLE_ID):
            await ctx.send("❌ У вас немає прав.")
            return

        # удаляем сообщение команды
        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="Повідомити про баг",
            description=FIRST_MESSAGE,
            color=0x0087E6
        )

        await ctx.send(embed=embed, view=TicketView())


async def setup(bot):
    await bot.add_cog(Ticket(bot))
