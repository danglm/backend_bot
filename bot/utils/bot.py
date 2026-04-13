from pyrogram import Client
from bot.core.config import settings

bot = Client(
    name="bot",
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
    bot_token=settings.BOT_TOKEN,
    workdir="."
)
