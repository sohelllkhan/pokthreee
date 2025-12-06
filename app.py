import discord
from discord.ext import commands, tasks
import os
import random
import ast

# ===============================
# CONFIG
# ===============================
TOKEN = os.getenv("DISCORD_TOKEN") 
CHANNEL_ID = os.getenv("DISCORD_CHANNEL") 
POKE_FOLDER = "pokemon_images"
ALT_FILE = "alt.txt"

# ===============================
# INTENTS
# ===============================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===============================
# LOAD DICTIONARY
# ===============================
with open(ALT_FILE, "r", encoding="utf-8") as f:
    pokemon_dict = ast.literal_eval(f.read())

# ===============================
# VARIABLES
# ===============================
swap_active = False
serial_mode = False
random_mode = False
name_mode = False      # NEW MODE
swap_time = 15
current_index = 0
current_pokemon = None
last_pokemon = None

# sorted by names (for pname)
sorted_by_name = sorted(pokemon_dict.items(), key=lambda x: x[1].lower())
name_keys = [k for k, v in sorted_by_name]


# ===============================
# CREATE DYNAMIC LOOP
# ===============================
def create_swap_loop(seconds):
    @tasks.loop(seconds=seconds)
    async def loop():
        await pokemon_swap()
    return loop


swap_loop = create_swap_loop(swap_time)


# ===============================
# THE SWAP FUNCTION
# ===============================
async def pokemon_swap():
    global current_index, current_pokemon, last_pokemon

    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        return

    # ========== PICK POKEMON KEY ==========
    if serial_mode:
        keys = list(pokemon_dict.keys())
        poke_key = keys[current_index % len(keys)]
        current_index += 1

    elif random_mode:
        poke_key = random.choice(list(pokemon_dict.keys()))

    elif name_mode:
        poke_key = name_keys[current_index % len(name_keys)]
        current_index += 1

    else:
        return

    # ========== UPDATE NAMES ==========
    last_pokemon = current_pokemon
    current_pokemon = pokemon_dict[poke_key]

    if last_pokemon:
        await channel.send(f"Previous Pokémon was **{last_pokemon}**")

    # ========== SEND IMAGE ==========
    img_path = f"{POKE_FOLDER}/{poke_key}.png"
    if not os.path.exists(img_path):
        await channel.send(f"⚠ Missing image `{poke_key}.png`")
        return

    file = discord.File(img_path)
    await channel.send("New Pokémon appeared! Use **!c <name>**", file=file)


# ===============================
# START
# ===============================
@bot.command()
async def pstart(ctx):
    global swap_active, swap_loop
    if ctx.channel.id != CHANNEL_ID:
        return

    if swap_active:
        await ctx.send("Already running!")
        return

    swap_active = True
    swap_loop.start()
    await ctx.send(f"🟢 Pokémon swap started! Interval {swap_time}s")


# ===============================
# STOP
# ===============================
@bot.command()
async def pend(ctx):
    global swap_active, swap_loop
    if swap_loop.is_running():
        swap_loop.stop()
    swap_active = False
    await ctx.send("🔴 Swap stopped.")


# ===============================
# SET TIME COMMAND
# ===============================
@bot.command()
async def s(ctx, seconds: int):
    global swap_time, swap_loop, swap_active

    if ctx.channel.id != CHANNEL_ID:
        return

    if seconds < 1:
        await ctx.send("Minimum is 1 second.")
        return

    swap_time = seconds

    if swap_active:
        swap_loop.stop()
        swap_loop = create_swap_loop(swap_time)
        swap_loop.start()

    await ctx.send(f"⏱ Swap interval updated to **{seconds}s**")


# ===============================
# RANDOM MODE
# ===============================
@bot.command()
async def prandom(ctx):
    global random_mode, serial_mode, name_mode
    random_mode = True
    serial_mode = False
    name_mode = False
    await ctx.send("🌀 Random swap mode activated!")


# ===============================
# SERIAL MODE
# ===============================
@bot.command()
async def pserial(ctx):
    global random_mode, serial_mode, name_mode
    serial_mode = True
    random_mode = False
    name_mode = False
    await ctx.send("📜 Serial swap mode (file-order) activated!")


# ===============================
# NAME SERIAL MODE (NEW)
# ===============================
@bot.command()
async def pname(ctx):
    global random_mode, serial_mode, name_mode, current_index
    name_mode = True
    random_mode = False
    serial_mode = False
    current_index = 0
    await ctx.send("🔤 Name-order swap mode activated!")


# ===============================
# CATCH COMMAND
# ===============================
@bot.command()
async def c(ctx, *, name: str):
    global current_pokemon

    if ctx.channel.id != CHANNEL_ID:
        return

    if not current_pokemon:
        await ctx.send("No Pokémon right now!")
        return

    if name.lower().strip() == current_pokemon.lower():
        await ctx.send(f"🎉 You caught **{current_pokemon}**!")
        current_pokemon = None
    else:
        await ctx.send("❌ Wrong name!")


# ===============================
# READY
# ===============================
@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user}")


bot.run(TOKEN)
