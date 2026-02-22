import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import discord
from discord.ext import commands

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return  # silence default HTTP logs


def run_http_server():
    port = int(os.getenv("PORT", "8080"))  # Render provides PORT
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


threading.Thread(target=run_http_server, daemon=True).start()


intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    # Load extension once
    if not getattr(bot, "_cogs_loaded", False):
        bot.load_extension("cogs.thread_actions")
        bot._cogs_loaded = True

bot.run(os.getenv("TOKEN"))
