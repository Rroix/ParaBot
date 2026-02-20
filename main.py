import os
import discord
from discord.ext import commands
from aiohttp import web

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

async def handle(request):
    return web.Response(text="OK")

async def start_webserver():
    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.loop.create_task(start_webserver())

bot.load_extension("cogs.thread_actions")

bot.run(TOKEN)