from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode, ChatMemberStatus
from bot.utils.bot import bot
from bot.utils.utils import check_command_target, command_timeout
from bot.utils.logger import LogInfo, LogError, LogType


@bot.on_message(filters.command(["get_chat_id", "lay_chat_id"]) | filters.regex(r"^@\w+\s+/(get_chat_id|lay_chat_id)\b"))
@command_timeout(auto_delete_cmd=True)
async def get_chat_id_handler(client, message: Message) -> None:
    """Lấy Chat ID của nhóm hiện tại.

    Kiểm tra quyền trực tiếp từ Telegram (giống /syncchat) chứ không qua CSDL,
    để vẫn dùng được ở nhóm chưa đồng bộ — đó chính là lúc cần biết Chat ID nhất.
    """
    args = await check_command_target(client, message.text, ["get_chat_id", "lay_chat_id"])
    if args is None: return

    try:
        if message.from_user:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if member.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
                await message.reply_text("⚠️ Chỉ <b>Owner</b> và <b>Admin</b> mới được sử dụng lệnh này.", parse_mode=ParseMode.HTML)
                return
        elif message.sender_chat and message.sender_chat.id == message.chat.id:
            # Admin ẩn danh đăng dưới danh nghĩa nhóm
            pass
        else:
            await message.reply_text("⚠️ Không thể xác định người dùng. Chỉ <b>Owner</b> và <b>Admin</b> mới được sử dụng lệnh này.", parse_mode=ParseMode.HTML)
            return
    except Exception as e:
        LogError(f"[GetChatID] Error checking permission: {e}", LogType.SYSTEM_STATUS)
        await message.reply_text("❌ Không thể kiểm tra quyền hạn của bạn.")
        return

    await message.reply_text(
        f"Thông tin chat_id: <code>{message.chat.id}</code>",
        parse_mode=ParseMode.HTML
    )
    LogInfo(f"[GetChatID] {message.chat.title} -> {message.chat.id}", LogType.SYSTEM_STATUS)
