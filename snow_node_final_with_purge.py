
# SNOW NODE VPS BOT - FINAL (WITH GLOBAL PURGE SYSTEM)
# Added by request:
# !purge        -> Main admin only, deletes ALL VPS except safelisted
# !purge-s ID   -> Safelist VPS container from purge
# After purge   -> Safelist auto-cleared

import discord
from discord.ext import commands, tasks
import asyncio, subprocess, json, os, shlex, shutil, threading, time
from datetime import datetime

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "1210291131301101618"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ---------------- DATA ----------------
def load_json(name, default):
    try:
        with open(name, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(name, data):
    with open(name, "w") as f:
        json.dump(data, f, indent=4)

vps_data = load_json("vps_data.json", {})
admin_data = load_json("admin_data.json", {"admins": []})
purge_safe = load_json("purge_safe.json", [])  # list of container names

# ---------------- CHECKS ----------------
def is_main_admin():
    async def predicate(ctx):
        if ctx.author.id != MAIN_ADMIN_ID:
            raise commands.CheckFailure("Only MAIN ADMIN can use this command.")
        return True
    return commands.check(predicate)

# ---------------- HELPERS ----------------
async def run(cmd):
    p = await asyncio.create_subprocess_exec(
        *shlex.split(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    out, err = await p.communicate()
    if p.returncode != 0:
        raise Exception(err.decode())
    return out.decode()

def embed(title, desc, color=0x2b2d31):
    e = discord.Embed(title=title, description=desc, color=color)
    e.set_footer(text="SNOW NODE • MADE BY GG")
    return e

# ---------------- COMMANDS ----------------
@bot.command(name="purge")
@is_main_admin()
async def purge_all(ctx):
    deleted = []
    skipped = []

    for user_id, vps_list in list(vps_data.items()):
        for vps in list(vps_list):
            name = vps["container_name"]
            if name in purge_safe:
                skipped.append(name)
                continue
            try:
                await run(f"lxc delete {name} --force")
                deleted.append(name)
            except:
                pass
        vps_data[user_id] = [
            v for v in vps_list if v["container_name"] in purge_safe
        ]
        if not vps_data[user_id]:
            del vps_data[user_id]

    save_json("vps_data.json", vps_data)

    # CLEAR SAFE LIST AFTER PURGE
    purge_safe.clear()
    save_json("purge_safe.json", purge_safe)

    await ctx.send(embed(
        "🔥 GLOBAL VPS PURGE COMPLETE",
        f"**Deleted VPS:** {len(deleted)}
"
        f"**Safelisted (Skipped):** {len(skipped)}

"
        f"Safelist auto-cleared.",
        0xff0000
    ))

@bot.command(name="purge-s")
@is_main_admin()
async def purge_safe_add(ctx, container_name: str):
    if container_name not in purge_safe:
        purge_safe.append(container_name)
        save_json("purge_safe.json", purge_safe)
        await ctx.send(embed(
            "🛡 VPS SAFELISTED",
            f"`{container_name}` is now SAFE from `!purge`",
            0x00ff88
        ))
    else:
        await ctx.send(embed(
            "ℹ Already Safe",
            f"`{container_name}` is already in safelist"
        ))

@bot.event
async def on_ready():
    print("SNOW NODE BOT READY")

bot.run(DISCORD_TOKEN)
