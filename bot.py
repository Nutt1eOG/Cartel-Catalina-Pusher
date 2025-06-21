# opgave_bot.py
import discord
import logging
import os
import sys
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger('discord_bot')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# In production (like Render), we'll rely on console logging
# In development, we'll also log to a file if possible
if os.getenv('RENDER') != 'true':
    try:
        file_handler = logging.FileHandler('discord_bot.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info("File logging enabled")
    except Exception as e:
        logger.warning(f"Could not set up file logging: {e}")
else:
    logger.info("Running in Render environment, using console logging only")

# Load environment variables
# In development, load from .env file
# In production (Render), environment variables are set in the dashboard
if os.getenv('RENDER') != 'true':
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
else:
    logger.info("Using environment variables from Render")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

OPGAVE_KANAL_NAVN = os.getenv("OPGAVE_KANAL_NAVN", "opgaver")
KLAREDE_KANAL_NAVN = os.getenv("KLAREDE_KANAL_NAVN", "klarede-opgaver")

# Initialize channel IDs with None to indicate they should be set dynamically
# This is better for deployment where we don't want to rely on hardcoded IDs
OPGAVE_KANAL_ID = None
KLAREDE_KANAL_ID = None

# Try to get channel IDs from environment variables if they exist
opgave_id_str = os.getenv("OPGAVE_KANAL_ID")
if opgave_id_str:
    try:
        OPGAVE_KANAL_ID = int(opgave_id_str)
        logger.info(f"Using OPGAVE_KANAL_ID from environment: {OPGAVE_KANAL_ID}")
    except ValueError:
        logger.warning(f"Invalid OPGAVE_KANAL_ID in environment variables: {opgave_id_str}")

klarede_id_str = os.getenv("KLAREDE_KANAL_ID")
if klarede_id_str:
    try:
        KLAREDE_KANAL_ID = int(klarede_id_str)
        logger.info(f"Using KLAREDE_KANAL_ID from environment: {KLAREDE_KANAL_ID}")
    except ValueError:
        logger.warning(f"Invalid KLAREDE_KANAL_ID in environment variables: {klarede_id_str}")

FULDGYLDIG_ROLLER = ["Fuldgyldigt", "Ledelse"]
PUSHER_ROLLE = "Pusher"

class OpgaveView(discord.ui.View):
    def __init__(self, opgave, opretter_id):
        super().__init__(timeout=None)
        self.opgave = opgave
        self.opretter_id = opretter_id
        self.tager_id = None

    @discord.ui.button(label="Tag opgave", style=discord.ButtonStyle.primary)
    async def tag_opgave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if PUSHER_ROLLE not in [role.name for role in interaction.user.roles]:
            return await interaction.response.send_message("Du skal være pusher for at tage opgaver!", ephemeral=True)
        self.tager_id = interaction.user.id
        self.clear_items()
        self.add_item(MarkerKlarButton(self.opgave, self.opretter_id, interaction.user.id))
        await interaction.response.edit_message(content=f"🧾 Opgave: **{self.opgave}**\n👤 Tager: {interaction.user.mention}", view=self)

class MarkerKlarButton(discord.ui.Button):
    def __init__(self, opgave, opretter_id, tager_id):
        super().__init__(label="Marker som klaret", style=discord.ButtonStyle.success)
        self.opgave = opgave
        self.opretter_id = opretter_id
        self.tager_id = tager_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.tager_id:
            return await interaction.response.send_message("Kun den der tog opgaven kan markere den som klaret!", ephemeral=True)

        # Send message to the completed tasks channel
        klarede_kanal = interaction.client.get_channel(KLAREDE_KANAL_ID)
        if klarede_kanal:
            await klarede_kanal.send(
                f"✅ Opgave klaret!\n🧾 **{self.opgave}**\n👤 Tager: <@{self.tager_id}>\n📨 Oprettet af: <@{self.opretter_id}>"
            )

        # Send direct message to the task creator
        try:
            # Get the task creator user object
            guild = interaction.guild
            creator = await guild.fetch_member(self.opretter_id)
            taker = await guild.fetch_member(self.tager_id)

            if creator:
                # Send notification message to the task creator
                await creator.send(
                    f"🎉 **Din opgave er blevet løst!**\n\n"
                    f"🧾 **Opgave:** {self.opgave}\n"
                    f"👤 **Løst af:** {taker.display_name}\n\n"
                    f"Opgaven er nu markeret som afsluttet. Tak for at bruge opgavesystemet!"
                )
                logger.info(f"Sent completion notification to task creator {creator.display_name}")
        except Exception as e:
            logger.error(f"Failed to send notification to task creator: {e}")

        # Acknowledge the interaction and delete the original message
        await interaction.response.send_message("Opgave markeret som klaret!", ephemeral=True)
        await interaction.message.delete()

@bot.event
async def on_ready():
    global OPGAVE_KANAL_ID, KLAREDE_KANAL_ID
    logger.info(f"Bot is ready as {bot.user}")

    # Check if bot is in any guilds
    if not bot.guilds:
        logger.warning("Bot is not in any guilds. Waiting for invitations.")
        return

    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    try:
        guild = bot.guilds[0]
        logger.info(f"Setting up channels and roles for guild: {guild.name} (ID: {guild.id})")

        # Create channels if they don't exist
        try:
            opgave_kanal = discord.utils.get(guild.text_channels, name=OPGAVE_KANAL_NAVN)
            if not opgave_kanal:
                logger.info(f"Creating channel: {OPGAVE_KANAL_NAVN}")
                opgave_kanal = await guild.create_text_channel(OPGAVE_KANAL_NAVN)
            if opgave_kanal:
                OPGAVE_KANAL_ID = opgave_kanal.id
                logger.info(f"Using task channel: {opgave_kanal.name} (ID: {OPGAVE_KANAL_ID})")
            else:
                logger.error(f"Failed to find or create task channel: {OPGAVE_KANAL_NAVN}")
        except Exception as e:
            logger.error(f"Error setting up task channel: {e}")

        try:
            klarede_kanal = discord.utils.get(guild.text_channels, name=KLAREDE_KANAL_NAVN)
            if not klarede_kanal:
                logger.info(f"Creating channel: {KLAREDE_KANAL_NAVN}")
                klarede_kanal = await guild.create_text_channel(KLAREDE_KANAL_NAVN)
            if klarede_kanal:
                KLAREDE_KANAL_ID = klarede_kanal.id
                logger.info(f"Using completed tasks channel: {klarede_kanal.name} (ID: {KLAREDE_KANAL_ID})")
            else:
                logger.error(f"Failed to find or create completed tasks channel: {KLAREDE_KANAL_NAVN}")
        except Exception as e:
            logger.error(f"Error setting up completed tasks channel: {e}")

        # Create roles if they don't exist
        try:
            # Create Pusher role
            pusher_role = discord.utils.get(guild.roles, name=PUSHER_ROLLE)
            if not pusher_role:
                logger.info(f"Creating {PUSHER_ROLLE} role")
                await guild.create_role(name=PUSHER_ROLLE, color=discord.Color.blue(), 
                                      reason="Role for users who can take tasks")
                logger.info(f"Created {PUSHER_ROLLE} role successfully")

            # Create Fuldgyldigt and Ledelse roles
            for role_name in FULDGYLDIG_ROLLER:
                role = discord.utils.get(guild.roles, name=role_name)
                if not role:
                    logger.info(f"Creating {role_name} role")
                    color = discord.Color.gold() if role_name == "Ledelse" else discord.Color.green()
                    await guild.create_role(name=role_name, color=color, 
                                          reason="Role for users who can create tasks")
                    logger.info(f"Created {role_name} role successfully")
        except Exception as e:
            logger.error(f"Error setting up roles: {e}")

        # Sync application commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synchronized {len(synced)} commands successfully")
        except Exception as e:
            logger.error(f"Error synchronizing commands: {e}")

    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")

    logger.info("Bot initialization complete")

@bot.tree.command(name="opretopgave", description="Opret en ny opgave")
@app_commands.describe(opgave="Beskriv opgaven", pris="Sæt prisen (valgfrit)")
async def opretopgave(interaction: discord.Interaction, opgave: str, pris: str = None):
    try:
        # Check if user has permission
        if not any(role.name in FULDGYLDIG_ROLLER for role in interaction.user.roles):
            logger.warning(f"User {interaction.user.name} (ID: {interaction.user.id}) attempted to create a task without permission")
            return await interaction.response.send_message("Du har ikke tilladelse til at oprette opgaver.", ephemeral=True)

        # Get the task channel
        if OPGAVE_KANAL_ID is None:
            logger.error("Task channel ID is not set")
            return await interaction.response.send_message("Fejl: Opgavekanal er ikke konfigureret. Kontakt en administrator.", ephemeral=True)

        kanal = bot.get_channel(OPGAVE_KANAL_ID)
        if not kanal:
            # Try to find the channel by name as a fallback
            logger.warning(f"Could not find channel with ID {OPGAVE_KANAL_ID}, trying to find by name")
            guild = interaction.guild
            kanal = discord.utils.get(guild.text_channels, name=OPGAVE_KANAL_NAVN)

            if not kanal:
                logger.error(f"Task channel not found by ID or name")
                return await interaction.response.send_message("Fejl: Opgavekanal ikke fundet. Kontakt en administrator.", ephemeral=True)

        # Create and send the task
        logger.info(f"Creating task: '{opgave}' by user {interaction.user.name} (ID: {interaction.user.id})")
        pris_tekst = f"\n💰 Pris: {pris}" if pris else ""
        embed = discord.Embed(
            title="📌 Ny opgave",
            description=f"🧾 {opgave}{pris_tekst}\n📝 Oprettet af: {interaction.user.mention}",
            color=discord.Color.orange()
        )
        view = OpgaveView(opgave, interaction.user.id)
        await kanal.send(embed=embed, view=view)
        await interaction.response.send_message("Opgave oprettet.", ephemeral=True)
        logger.info(f"Task created successfully")

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        await interaction.response.send_message("Der opstod en fejl ved oprettelse af opgaven. Prøv igen senere.", ephemeral=True)

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        logger.critical("No Discord token found.")
        sys.exit(1)
    bot.run(TOKEN)
