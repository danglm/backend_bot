from pyrogram import Client
from bot.core.config import settings

bot = Client(
    name="bot",
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
    bot_token=settings.BOT_TOKEN,
    workdir=".",
    # Các luồng nút bấm sửa đi sửa lại cùng một tin nhắn nên hay dính FLOOD_WAIT trên
    # messages.EditMessage. Mặc định của Pyrogram là 10s: quá ngưỡng là ném thẳng ra
    # handler. Nới lên 30s để Pyrogram tự ngủ rồi thử lại — vẫn dưới COMMAND_TIMEOUT
    # (60s) nên asyncio.wait_for của command_timeout không cắt ngang.
    sleep_threshold=30,
)
