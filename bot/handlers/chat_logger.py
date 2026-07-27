import os
import datetime
from typing import List
from pyrogram import filters
from pyrogram.types import Message
from bot.utils.bot import bot
from bot.core.config import settings
from bot.utils.logger import LogInfo, LogError, LogType
from app.db.session import SessionLocal
from app.models.telegram import TelegramProjectMember
from app.models.chat import TelegramChatMessage, TelegramChatMessageEdit, TelegramChatAttachment
from app.services.chat_socket import chat_ws_manager


async def _save_media_attachment(client, message: Message, db_msg_id) -> bool:
    """Tải và lưu thông tin media đính kèm vào đĩa Server và CSDL."""
    db = SessionLocal()
    try:
        media_obj = None
        file_type = "other"
        file_name = None
        mime_type = None
        file_size = None

        if message.photo:
            media_obj = message.photo
            file_type = "photo"
            file_name = f"photo_{message.chat.id}_{message.id}.jpg"
            mime_type = "image/jpeg"
        elif message.document:
            media_obj = message.document
            file_type = "document"
            file_name = message.document.file_name or f"doc_{message.id}"
            mime_type = message.document.mime_type
            file_size = message.document.file_size
        elif message.voice:
            media_obj = message.voice
            file_type = "voice"
            file_name = f"voice_{message.id}.ogg"
            mime_type = message.voice.mime_type or "audio/ogg"
            file_size = message.voice.file_size
        elif message.video:
            media_obj = message.video
            file_type = "video"
            file_name = message.video.file_name or f"video_{message.id}.mp4"
            mime_type = message.video.mime_type or "video/mp4"
            file_size = message.video.file_size
        elif message.audio:
            media_obj = message.audio
            file_type = "audio"
            file_name = message.audio.file_name or f"audio_{message.id}.mp3"
            mime_type = message.audio.mime_type or "audio/mpeg"
            file_size = message.audio.file_size
        elif message.sticker:
            media_obj = message.sticker
            file_type = "sticker"
            file_name = f"sticker_{message.id}.webp"
            mime_type = "image/webp"

        if not media_obj:
            return False

        file_id = getattr(media_obj, "file_id", str(message.id))
        file_unique_id = getattr(media_obj, "file_unique_id", None)
        if hasattr(media_obj, "file_size") and not file_size:
            file_size = getattr(media_obj, "file_size", None)

        # Tạo đường dẫn lưu file: uploads/chat_media/YYYY/MM/
        now = datetime.datetime.now()
        relative_dir = os.path.join(settings.MEDIA_STORAGE_PATH, f"{now.year}", f"{now.month:02d}")
        abs_dir = os.path.join(os.getcwd(), relative_dir)
        os.makedirs(abs_dir, exist_ok=True)

        target_file_path = os.path.join(abs_dir, f"{message.id}_{file_name}")
        local_relative_path = os.path.join(relative_dir, f"{message.id}_{file_name}").replace("\\", "/")

        # Tải file từ Telegram Pyrogram
        try:
            await client.download_media(message, file_name=target_file_path)
            LogInfo(f"[ChatLogger] Saved media for msg {message.id} to {local_relative_path}", LogType.SYSTEM_STATUS)
        except Exception as dl_err:
            LogError(f"[ChatLogger] Failed to download media for msg {message.id}: {dl_err}", LogType.SYSTEM_STATUS)
            local_relative_path = None

        attachment = TelegramChatAttachment(
            message_db_id=db_msg_id,
            file_type=file_type,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            local_path=local_relative_path
        )
        db.add(attachment)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        LogError(f"[ChatLogger] Error saving attachment for msg {message.id}: {e}", LogType.SYSTEM_STATUS)
        return False
    finally:
        db.close()


@bot.on_message(group=10)
async def chat_message_logger_handler(client, message: Message) -> None:
    """Tự động ghi nhận mọi tin nhắn mới từ các nhóm Telegram đã syncchat."""
    if not settings.ENABLE_AUTO_SAVE_CHAT_LOGS:
        return

    if not message.chat:
        return

    chat_id_str = str(message.chat.id)

    db = SessionLocal()
    try:
        # Kiểm tra nhóm này có thuộc CSDL TelegramProjectMember không (đã syncchat)
        synced_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id_str
        ).first()

        if not synced_member:
            return

        project_id = synced_member.project_id
        group_name = message.chat.title or synced_member.group_name

        user_id = str(message.from_user.id) if message.from_user else None
        username = message.from_user.username if message.from_user else None
        full_name = None
        is_bot = False

        if message.from_user:
            fn = message.from_user.first_name or ""
            ln = message.from_user.last_name or ""
            full_name = f"{fn} {ln}".strip() or username or user_id
            is_bot = message.from_user.is_bot
        elif message.sender_chat:
            full_name = message.sender_chat.title or "Channel"

        # Determine message_type
        message_type = "text"
        has_media = False
        text_content = message.text or message.caption or ""

        if message.photo:
            message_type = "photo"
            has_media = True
        elif message.document:
            message_type = "document"
            has_media = True
        elif message.voice:
            message_type = "voice"
            has_media = True
        elif message.video:
            message_type = "video"
            has_media = True
        elif message.audio:
            message_type = "audio"
            has_media = True
        elif message.sticker:
            message_type = "sticker"
            has_media = True
        elif message.service:
            message_type = "service"

        reply_to_msg_id = message.reply_to_message.id if message.reply_to_message else None
        reply_to_u_id = str(message.reply_to_message.from_user.id) if (message.reply_to_message and message.reply_to_message.from_user) else None
        thread_id = getattr(message, "message_thread_id", None)

        msg_date = message.date if message.date else datetime.datetime.now()

        # Check for existing record to avoid duplicate
        existing = db.query(TelegramChatMessage).filter(
            TelegramChatMessage.chat_id == chat_id_str,
            TelegramChatMessage.message_id == message.id
        ).first()

        if existing:
            return

        new_chat_msg = TelegramChatMessage(
            message_id=message.id,
            chat_id=chat_id_str,
            group_name=group_name,
            project_id=project_id,
            user_id=user_id,
            username=username,
            full_name=full_name,
            is_bot=is_bot,
            message_type=message_type,
            text_content=text_content,
            reply_to_message_id=reply_to_msg_id,
            reply_to_user_id=reply_to_u_id,
            thread_id=thread_id,
            has_media=has_media,
            date=msg_date
        )
        db.add(new_chat_msg)
        db.commit()
        db.refresh(new_chat_msg)

        # Lưu media đính kèm nếu có
        attachments_list = []
        if has_media:
            await _save_media_attachment(client, message, new_chat_msg.id)
            att_records = db.query(TelegramChatAttachment).filter(
                TelegramChatAttachment.message_db_id == new_chat_msg.id
            ).all()
            for att in att_records:
                attachments_list.append({
                    "id": str(att.id),
                    "file_type": att.file_type,
                    "file_id": att.file_id,
                    "file_name": att.file_name,
                    "file_size": att.file_size,
                    "mime_type": att.mime_type,
                    "download_url": f"/api/v1/telegram/chat/media/{att.id}" if att.local_path else None
                })

        # Broadcast event WebSocket real-time cho Web Frontend
        msg_dict = {
            "id": str(new_chat_msg.id),
            "message_id": new_chat_msg.message_id,
            "chat_id": new_chat_msg.chat_id,
            "group_name": new_chat_msg.group_name,
            "project_id": str(new_chat_msg.project_id) if new_chat_msg.project_id else None,
            "user_id": new_chat_msg.user_id,
            "username": new_chat_msg.username,
            "full_name": new_chat_msg.full_name,
            "is_bot": new_chat_msg.is_bot,
            "is_mine": False,
            "message_type": new_chat_msg.message_type,
            "text_content": new_chat_msg.text_content,
            "reply_to_message_id": new_chat_msg.reply_to_message_id,
            "has_media": new_chat_msg.has_media,
            "attachments": attachments_list,
            "date": new_chat_msg.date.isoformat() if new_chat_msg.date else None,
            "created_at": new_chat_msg.created_at.isoformat() if new_chat_msg.created_at else None
        }
        await chat_ws_manager.broadcast_event("NEW_MESSAGE", msg_dict)

    except Exception as e:
        db.rollback()
        LogError(f"[ChatLogger] Error logging message {message.id} in chat {chat_id_str}: {e}", LogType.SYSTEM_STATUS)
    finally:
        db.close()


@bot.on_edited_message(group=10)
async def chat_edited_message_logger_handler(client, message: Message) -> None:
    """Tự động cập nhật nội dung mới và lưu vết lịch sử cũ khi tin nhắn bị sửa."""
    if not settings.ENABLE_AUTO_SAVE_CHAT_LOGS:
        return

    if not message.chat:
        return

    chat_id_str = str(message.chat.id)

    db = SessionLocal()
    try:
        existing = db.query(TelegramChatMessage).filter(
            TelegramChatMessage.chat_id == chat_id_str,
            TelegramChatMessage.message_id == message.id
        ).first()

        if not existing:
            return

        new_text = message.text or message.caption or ""
        old_text = existing.text_content or ""

        if new_text != old_text:
            # Save edit history
            edit_history = TelegramChatMessageEdit(
                message_db_id=existing.id,
                old_text_content=old_text,
                edited_at=datetime.datetime.now()
            )
            db.add(edit_history)

            existing.text_content = new_text
            existing.is_edited = True
            existing.edited_at = message.edit_date or datetime.datetime.now()
            db.commit()

            # Broadcast WebSocket event
            await chat_ws_manager.broadcast_event("MESSAGE_EDITED", {
                "id": str(existing.id),
                "chat_id": chat_id_str,
                "message_id": message.id,
                "text_content": new_text,
                "old_text_content": old_text,
                "edited_at": existing.edited_at.isoformat() if existing.edited_at else None
            })

    except Exception as e:
        db.rollback()
        LogError(f"[ChatLogger] Error handling edit for msg {message.id} in chat {chat_id_str}: {e}", LogType.SYSTEM_STATUS)
    finally:
        db.close()


@bot.on_deleted_messages(group=10)
async def chat_deleted_message_logger_handler(client, messages: List[Message]) -> None:
    """Tự động cập nhật cờ is_deleted=True và phát sự kiện WebSocket MESSAGE_DELETED khi tin nhắn bị xóa trên Telegram."""
    if not settings.ENABLE_AUTO_SAVE_CHAT_LOGS:
        LogInfo("[ChatLogger Delete] Handler skipped because ENABLE_AUTO_SAVE_CHAT_LOGS is False", LogType.SYSTEM_STATUS)
        return

    LogInfo(f"[ChatLogger Delete Event Triggered] Received {len(messages)} deleted message(s) update from Telegram API", LogType.SYSTEM_STATUS)

    db = SessionLocal()
    try:
        for msg in messages:
            msg_id = getattr(msg, "id", None) or getattr(msg, "message_id", None)
            chat_id_str = str(msg.chat.id) if (hasattr(msg, "chat") and msg.chat) else None

            LogInfo(f"[ChatLogger Delete Processing] Raw event item -> msg_id={msg_id}, chat_id={chat_id_str}", LogType.SYSTEM_STATUS)

            if not msg_id:
                LogWarning(f"[ChatLogger Delete Warning] Cannot extract valid msg_id from Telegram event: {msg}", LogType.SYSTEM_STATUS)
                continue

            query = db.query(TelegramChatMessage).filter(
                TelegramChatMessage.message_id == msg_id,
                TelegramChatMessage.is_deleted == False
            )
            if chat_id_str:
                query = query.filter(TelegramChatMessage.chat_id == chat_id_str)

            existing_msgs = query.all()
            if not existing_msgs:
                LogWarning(f"[ChatLogger Delete Warning] No active DB record found in telegram_chat_messages for msg_id={msg_id} (chat_id={chat_id_str})", LogType.SYSTEM_STATUS)
                continue

            for existing in existing_msgs:
                existing.is_deleted = True
                existing.deleted_at = datetime.datetime.now()
                db.commit()

                LogInfo(f"[ChatLogger Delete Success] Marked message_id={existing.message_id} (DB id={existing.id}) as deleted in chat {existing.chat_id}", LogType.SYSTEM_STATUS)
                await chat_ws_manager.broadcast_event("MESSAGE_DELETED", {
                    "id": str(existing.id),
                    "chat_id": existing.chat_id,
                    "message_id": existing.message_id
                })

    except Exception as e:
        db.rollback()
        LogError(f"[ChatLogger Delete Error] Failed to process deleted messages: {e}", LogType.SYSTEM_STATUS)
    finally:
        db.close()


async def log_bot_outgoing_message(message: Message, db=None) -> None:
    """Hàm helper lưu và phát WebSocket khi Bot phản hồi tin nhắn trong nhóm Telegram."""
    if not settings.ENABLE_AUTO_SAVE_CHAT_LOGS or not message or not message.chat:
        return

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        chat_id_str = str(message.chat.id)
        synced_member = db.query(TelegramProjectMember).filter(
            TelegramProjectMember.chat_id == chat_id_str
        ).first()

        project_id = synced_member.project_id if synced_member else None
        group_name = message.chat.title or (synced_member.group_name if synced_member else None)

        text_content = message.text or message.caption or ""
        message_type = "text"
        has_media = False

        if message.photo:
            message_type = "photo"
            has_media = True
        elif message.document:
            message_type = "document"
            has_media = True

        reply_to_msg_id = message.reply_to_message.id if message.reply_to_message else None

        # Check for existing record to avoid duplicate
        existing = db.query(TelegramChatMessage).filter(
            TelegramChatMessage.chat_id == chat_id_str,
            TelegramChatMessage.message_id == message.id
        ).first()

        if existing:
            return

        new_msg = TelegramChatMessage(
            message_id=message.id,
            chat_id=chat_id_str,
            group_name=group_name,
            project_id=project_id,
            user_id=str(bot.me.id) if (bot and bot.me) else "bot",
            username=bot.me.username if (bot and bot.me) else "bot",
            full_name=bot.me.first_name if (bot and bot.me) else "Bot",
            is_bot=True,
            message_type=message_type,
            text_content=text_content,
            reply_to_message_id=reply_to_msg_id,
            has_media=has_media,
            date=message.date or datetime.datetime.now()
        )
        db.add(new_msg)
        db.commit()
        db.refresh(new_msg)

        attachments_list = []
        if has_media:
            await _save_media_attachment(bot, message, new_msg.id)
            att_records = db.query(TelegramChatAttachment).filter(
                TelegramChatAttachment.message_db_id == new_msg.id
            ).all()
            for att in att_records:
                attachments_list.append({
                    "id": str(att.id),
                    "file_type": att.file_type,
                    "file_id": att.file_id,
                    "file_name": att.file_name,
                    "file_size": att.file_size,
                    "mime_type": att.mime_type,
                    "download_url": f"/api/v1/telegram/chat/media/{att.id}" if att.local_path else None
                })

        msg_dict = {
            "id": str(new_msg.id),
            "message_id": new_msg.message_id,
            "chat_id": new_msg.chat_id,
            "group_name": new_msg.group_name,
            "project_id": str(new_msg.project_id) if new_msg.project_id else None,
            "user_id": new_msg.user_id,
            "username": new_msg.username,
            "full_name": new_msg.full_name,
            "is_bot": True,
            "is_mine": False,
            "message_type": new_msg.message_type,
            "text_content": new_msg.text_content,
            "reply_to_message_id": new_msg.reply_to_message_id,
            "has_media": has_media,
            "attachments": attachments_list,
            "date": new_msg.date.isoformat() if new_msg.date else None,
            "created_at": new_msg.created_at.isoformat() if new_msg.created_at else None
        }
        await chat_ws_manager.broadcast_event("NEW_MESSAGE", msg_dict)
        LogInfo(f"[ChatLogger Outgoing] Saved bot response message_id={new_msg.message_id} in chat={new_msg.chat_id}", LogType.SYSTEM_STATUS)
    except Exception as e:
        if db:
            db.rollback()
        LogError(f"[ChatLogger] Error logging bot outgoing message: {e}", LogType.SYSTEM_STATUS)
    finally:
        if should_close and db:
            db.close()


async def log_bot_edited_outgoing_message(message: Message, db=None) -> None:
    """Hàm helper cập nhật CSDL và phát WebSocket khi Bot sửa nội dung tin nhắn (edit_text/edit_message_text)."""
    if not settings.ENABLE_AUTO_SAVE_CHAT_LOGS or not message or not message.chat:
        return

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        chat_id_str = str(message.chat.id)
        existing = db.query(TelegramChatMessage).filter(
            TelegramChatMessage.chat_id == chat_id_str,
            TelegramChatMessage.message_id == message.id
        ).first()

        new_text = message.text or message.caption or ""

        if existing:
            old_text = existing.text_content or ""
            if new_text != old_text:
                edit_history = TelegramChatMessageEdit(
                    message_db_id=existing.id,
                    old_text_content=old_text,
                    edited_at=datetime.datetime.now()
                )
                db.add(edit_history)

                existing.text_content = new_text
                existing.is_edited = True
                existing.edited_at = message.edit_date or datetime.datetime.now()
                db.commit()

                await chat_ws_manager.broadcast_event("MESSAGE_EDITED", {
                    "id": str(existing.id),
                    "chat_id": chat_id_str,
                    "message_id": message.id,
                    "text_content": new_text,
                    "old_text_content": old_text,
                    "edited_at": existing.edited_at.isoformat() if existing.edited_at else None
                })
                LogInfo(f"[ChatLogger Outgoing Edit] Updated bot message_id={message.id} in chat={chat_id_str}", LogType.SYSTEM_STATUS)
        else:
            await log_bot_outgoing_message(message, db=db)
    except Exception as e:
        if db:
            db.rollback()
        LogError(f"[ChatLogger] Error logging bot edited message: {e}", LogType.SYSTEM_STATUS)
    finally:
        if should_close and db:
            db.close()


def setup_bot_outgoing_logger():
    """Tự động hook vào Pyrogram Client để tự động bắt tất cả tin nhắn Bot gửi ra và sửa nội dung trên toàn hệ thống."""
    from pyrogram import Client

    orig_send_message = Client.send_message
    orig_send_photo = Client.send_photo
    orig_send_document = Client.send_document
    orig_edit_message_text = Client.edit_message_text

    async def patched_send_message(self, *args, **kwargs):
        msg = await orig_send_message(self, *args, **kwargs)
        try:
            if isinstance(msg, Message):
                await log_bot_outgoing_message(msg)
        except Exception as e:
            LogError(f"[ChatLogger Hook Error] send_message hook error: {e}", LogType.SYSTEM_STATUS)
        return msg

    async def patched_send_photo(self, *args, **kwargs):
        msg = await orig_send_photo(self, *args, **kwargs)
        try:
            if isinstance(msg, Message):
                await log_bot_outgoing_message(msg)
        except Exception as e:
            LogError(f"[ChatLogger Hook Error] send_photo hook error: {e}", LogType.SYSTEM_STATUS)
        return msg

    async def patched_send_document(self, *args, **kwargs):
        msg = await orig_send_document(self, *args, **kwargs)
        try:
            if isinstance(msg, Message):
                await log_bot_outgoing_message(msg)
        except Exception as e:
            LogError(f"[ChatLogger Hook Error] send_document hook error: {e}", LogType.SYSTEM_STATUS)
        return msg

    async def patched_edit_message_text(self, *args, **kwargs):
        msg = await orig_edit_message_text(self, *args, **kwargs)
        try:
            if isinstance(msg, Message):
                await log_bot_edited_outgoing_message(msg)
        except Exception as e:
            LogError(f"[ChatLogger Hook Error] edit_message_text hook error: {e}", LogType.SYSTEM_STATUS)
        return msg

    Client.send_message = patched_send_message
    Client.send_photo = patched_send_photo
    Client.send_document = patched_send_document
    Client.edit_message_text = patched_edit_message_text
    LogInfo("[ChatLogger] Auto-hook registered for Pyrogram outgoing Bot messages & edits", LogType.SYSTEM_STATUS)


# Kích hoạt hook tự động khi import chat_logger
setup_bot_outgoing_logger()




