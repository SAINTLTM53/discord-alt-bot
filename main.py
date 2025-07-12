import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import time

ALT_FILE = "alts.json"
TOKEN = os.getenv("BOT_TOKEN")
COOLDOWN_SECONDS = 5400  # 1 hour
CHANNEL_ID = 1393450041414254734

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.dm_messages = True
intents.guilds = True
intents.guild_messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

user_cooldowns = {}  # {user_id: timestamp}
sticky_message = None  # Last sticky message


def load_alts():
    if not os.path.exists(ALT_FILE):
        with open(ALT_FILE, "w") as f:
            json.dump([], f)
    with open(ALT_FILE, "r") as f:
        return json.load(f)


def save_alts(alts):
    with open(ALT_FILE, "w") as f:
        json.dump(alts, f, indent=4)


@bot.event
async def on_ready():
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync: {e}")
    print(f"✅ Logged in as {bot.user}")
    sticky_loop.start()


@tree.command(name="alts",
              description="Get a fresh Roblox alt account (1 per hour).")
async def get_alt(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = time.time()

    last_used = user_cooldowns.get(user_id, 0)
    time_left = (last_used + COOLDOWN_SECONDS) - now

    if time_left > 0:
        mins = int(time_left // 60)
        secs = int(time_left % 60)
        await interaction.response.send_message(
            f"⏳ You're on cooldown — try again in **{mins}m {secs}s**.",
            ephemeral=True,
        )
        return

    alts = load_alts()
    available = [alt for alt in alts if not alt.get("used")]

    if not available:
        await interaction.response.send_message(
            "Alts out of stock, sorry try again later.", ephemeral=True)
        return

    alt = available[0]
    alt["used"] = True
    save_alts(alts)

    try:
        await interaction.user.send(
            f"🎮 **Your Roblox Alt:**\n**Username:** `{alt['username']}`\n**Password:** `{alt['password']}`"
        )
        await interaction.response.send_message(
            "✅ Check your DMs For Your Aged Alt Account!", ephemeral=True)
        user_cooldowns[user_id] = now
    except:
        await interaction.response.send_message(
            "❌ Couldn't DM you. Please enable DMs.", ephemeral=True)


@bot.event
async def on_message(message):
    if message.channel.id == CHANNEL_ID:
        if message.author == bot.user:
            return

        # Allow admins to type freely
        if isinstance(message.author, discord.Member):
            if message.author.guild_permissions.administrator:
                return

        # Delete non-admin messages that aren't "/alts"
        if not message.content.strip().lower().startswith("/alts"):
            try:
                await message.delete()
            except:
                pass

    await bot.process_commands(message)


@tasks.loop(seconds=30)
async def sticky_loop():
    global sticky_message
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    # Delete previous sticky message
    if sticky_message:
        try:
            await sticky_message.delete()
        except:
            pass

    try:
        sticky_message = await channel.send(
            "📌 **Do `/alts` for free aged alt**")
    except Exception as e:
        print(f"Sticky message error: {e}")


bot.run(TOKEN)
